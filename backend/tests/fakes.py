"""In-memory implementations of repositories, for unit tests without a database."""

from collections.abc import Collection

from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges
from app.modules.users.models import User


class InMemoryIncidentRepository:
    def __init__(self, *incidents: Incident) -> None:
        self._incidents = {incident.id: incident for incident in incidents}

    def add(self, incident: Incident) -> Incident:
        incident.id = max(self._incidents, default=0) + 1
        incident.version = 1
        self._incidents[incident.id] = incident
        return incident

    def get(self, incident_id: int) -> Incident | None:
        return self._incidents.get(incident_id)

    def list_by_status(self, statuses: Collection[IncidentStatus]) -> list[Incident]:
        matching = (incident for incident in self._incidents.values() if incident.status in statuses)
        return sorted(matching, key=lambda incident: (incident.created_at, incident.id))

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident is None or incident.version != expected_version:
            return None
        for field, value in changes.items():
            setattr(incident, field, value)
        incident.version += 1
        return incident


class InMemoryUserRepository:
    def __init__(self, *users: User) -> None:
        self._users = {user.id: user for user in users}

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        return next((user for user in self._users.values() if user.username == username), None)

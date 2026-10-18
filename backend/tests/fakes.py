"""In-memory implementations of repositories, for unit tests without a database."""

from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges


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

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident is None or incident.version != expected_version:
            return None
        for field, value in changes.items():
            setattr(incident, field, value)
        incident.version += 1
        return incident

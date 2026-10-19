"""In-memory implementations of repositories, for unit tests without a database."""

from datetime import UTC, datetime

from app.modules.incidents.models import Incident, IncidentEvent
from app.modules.incidents.repository import IncidentChanges, IncidentFilter, IncidentOrder
from app.modules.users.models import User


class InMemoryIncidentRepository:
    def __init__(self, *incidents: Incident) -> None:
        self._incidents = {incident.id: incident for incident in incidents}
        self._event_ids = 0

    def add(self, incident: Incident) -> Incident:
        if incident.idempotency_key is not None:
            for existing in self._incidents.values():
                if (existing.reporter_id, existing.idempotency_key) == (incident.reporter_id, incident.idempotency_key):
                    return existing
        incident.id = max(self._incidents, default=0) + 1
        incident.version = 1
        self._incidents[incident.id] = incident
        return incident

    def get(self, incident_id: int) -> Incident | None:
        return self._incidents.get(incident_id)

    def search(self, criteria: IncidentFilter) -> list[Incident]:
        newest_first = criteria.order is not IncidentOrder.OLDEST_FIRST
        by_closing = criteria.order is IncidentOrder.RECENTLY_CLOSED_FIRST

        def sort_key(incident: Incident) -> tuple[bool, datetime, int]:
            moment = incident.closed_at if by_closing else incident.created_at
            # Same as the database: in descending order, a missing closing time goes last.
            return (moment is not None, moment or datetime.min.replace(tzinfo=UTC), incident.id)

        ordered = sorted(self._matching(criteria), key=sort_key, reverse=newest_first)
        end = None if criteria.limit is None else criteria.offset + criteria.limit
        return ordered[criteria.offset : end]

    def count(self, criteria: IncidentFilter) -> int:
        return len(self._matching(criteria))

    def _matching(self, criteria: IncidentFilter) -> list[Incident]:
        return [
            incident
            for incident in self._incidents.values()
            if (not criteria.statuses or incident.status in criteria.statuses)
            and (not criteria.criticalities or incident.criticality in criteria.criticalities)
            and (not criteria.categories or incident.category in criteria.categories)
            and (criteria.reporter_id is None or incident.reporter_id == criteria.reporter_id)
        ]

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident is None or incident.version != expected_version:
            return None
        for field, value in changes.items():
            setattr(incident, field, value)
        incident.version += 1
        return incident

    def add_event(self, event: IncidentEvent) -> IncidentEvent:
        # The event already sits in its incident's `events`, appended when `incident` was set.
        self._event_ids += 1
        event.id = self._event_ids
        event.created_at = datetime.now(UTC)
        return event


class InMemoryUserRepository:
    def __init__(self, *users: User) -> None:
        self._users = {user.id: user for user in users}

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        return next((user for user in self._users.values() if user.username == username), None)

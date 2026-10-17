from datetime import datetime
from typing import Protocol, TypedDict

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.models import Incident


class IncidentChanges(TypedDict, total=False):
    """Fields a use case may change on an existing incident."""

    status: IncidentStatus
    assignee_id: int | None
    closed_by_id: int | None
    closed_at: datetime | None
    closure_reason: str | None


class IncidentRepository(Protocol):
    def get(self, incident_id: int) -> Incident | None:
        """Return the current state of the incident, or None if it does not exist."""
        ...

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        """Apply `changes` and bump the version only if the stored version is `expected_version`.

        Returns None when the version does not match, meaning someone else changed the incident.
        """
        ...


class SqlAlchemyIncidentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, incident_id: int) -> Incident | None:
        return self._session.get(Incident, incident_id, populate_existing=True)

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        statement = (
            update(Incident)
            .where(Incident.id == incident_id, Incident.version == expected_version)
            .values(**changes, version=Incident.version + 1)
            .returning(Incident)
        )
        return self._session.scalars(statement).one_or_none()

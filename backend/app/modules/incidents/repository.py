from collections.abc import Collection
from datetime import datetime
from typing import Protocol, TypedDict

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

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
    def add(self, incident: Incident) -> Incident:
        """Persist a new incident and return it with its generated fields (id, version, timestamps)."""
        ...

    def get(self, incident_id: int) -> Incident | None:
        """Return the current state of the incident, or None if it does not exist."""
        ...

    def list_by_status(self, statuses: Collection[IncidentStatus]) -> list[Incident]:
        """Return the incidents in any of `statuses`, from the oldest to the newest, with their assignee loaded."""
        ...

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        """Apply `changes` and bump the version only if the stored version is `expected_version`.

        Returns None when the version does not match, meaning someone else changed the incident.
        """
        ...


class SqlAlchemyIncidentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, incident: Incident) -> Incident:
        self._session.add(incident)
        self._session.flush()
        self._session.refresh(incident)
        return incident

    def get(self, incident_id: int) -> Incident | None:
        return self._session.get(Incident, incident_id, populate_existing=True)

    def list_by_status(self, statuses: Collection[IncidentStatus]) -> list[Incident]:
        statement = (
            select(Incident)
            .where(Incident.status.in_(statuses))
            .order_by(Incident.created_at, Incident.id)
            .options(selectinload(Incident.assignee))
        )
        return list(self._session.scalars(statement))

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        statement = (
            update(Incident)
            .where(Incident.id == incident_id, Incident.version == expected_version)
            .values(**changes, version=Incident.version + 1)
            .returning(Incident)
            # RETURNING refreshes the columns but not relationships already loaded in the session (e.g. a stale assignee).
            .execution_options(populate_existing=True)
        )
        return self._session.scalars(statement).one_or_none()

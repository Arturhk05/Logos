from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, TypedDict
from uuid import UUID

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident


class IncidentChanges(TypedDict, total=False):
    """Fields a use case may change on an existing incident."""

    status: IncidentStatus
    assignee_id: int | None
    closed_by_id: int | None
    closed_at: datetime | None
    closure_reason: str | None


class IncidentOrder(Enum):
    OLDEST_FIRST = "oldest_first"
    NEWEST_FIRST = "newest_first"
    RECENTLY_CLOSED_FIRST = "recently_closed_first"


@dataclass(frozen=True)
class IncidentFilter:
    """Which incidents to search for. An empty collection or None means no filter on that field."""

    statuses: Collection[IncidentStatus] = ()
    criticalities: Collection[Criticality] = ()
    categories: Collection[IncidentCategory] = ()
    reporter_id: int | None = None
    order: IncidentOrder = IncidentOrder.OLDEST_FIRST
    offset: int = 0
    limit: int | None = None


class IncidentRepository(Protocol):
    def add(self, incident: Incident) -> Incident:
        """Persist a new incident and return it with its generated fields (id, version, timestamps).

        If its reporter already has an incident with the same idempotency key, nothing is inserted
        and that incident is returned instead.
        """
        ...

    def get(self, incident_id: int) -> Incident | None:
        """Return the current state of the incident, or None if it does not exist."""
        ...

    def search(self, criteria: IncidentFilter) -> list[Incident]:
        """Return the incidents matching `criteria`, in its order and page, with assignee and closed_by loaded.

        Ties in the order are broken by id, in the same direction.
        """
        ...

    def count(self, criteria: IncidentFilter) -> int:
        """Return how many incidents match `criteria`, ignoring its order and page."""
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
        try:
            with self._session.begin_nested():
                self._session.add(incident)
                self._session.flush()
        except IntegrityError:
            # The key was already used: a retry, or a concurrent request that committed first (the insert waits for it).
            # Under READ COMMITTED, PostgreSQL's default, the lookup below sees that committed incident.
            existing = self._find_by_idempotency_key(incident.reporter_id, incident.idempotency_key)
            if existing is None:
                raise
            return existing
        self._session.refresh(incident)
        return incident

    def get(self, incident_id: int) -> Incident | None:
        return self._session.get(Incident, incident_id, populate_existing=True)

    def search(self, criteria: IncidentFilter) -> list[Incident]:
        statement = (
            select(Incident)
            .where(*_conditions(criteria))
            .order_by(*_ORDER_BY[criteria.order])
            .offset(criteria.offset)
            .limit(criteria.limit)
            .options(selectinload(Incident.assignee), selectinload(Incident.closed_by))
        )
        return list(self._session.scalars(statement))

    def count(self, criteria: IncidentFilter) -> int:
        statement = select(func.count()).select_from(Incident).where(*_conditions(criteria))
        return self._session.scalars(statement).one()

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

    def _find_by_idempotency_key(self, reporter_id: int, key: UUID | None) -> Incident | None:
        if key is None:
            return None
        statement = select(Incident).where(Incident.reporter_id == reporter_id, Incident.idempotency_key == key)
        return self._session.scalars(statement).one_or_none()


_ORDER_BY: dict[IncidentOrder, tuple[ColumnElement[Any], ...]] = {
    IncidentOrder.OLDEST_FIRST: (Incident.created_at.asc(), Incident.id.asc()),
    IncidentOrder.NEWEST_FIRST: (Incident.created_at.desc(), Incident.id.desc()),
    IncidentOrder.RECENTLY_CLOSED_FIRST: (Incident.closed_at.desc().nulls_last(), Incident.id.desc()),
}


def _conditions(criteria: IncidentFilter) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if criteria.statuses:
        conditions.append(Incident.status.in_(criteria.statuses))
    if criteria.criticalities:
        conditions.append(Incident.criticality.in_(criteria.criticalities))
    if criteria.categories:
        conditions.append(Incident.category.in_(criteria.categories))
    if criteria.reporter_id is not None:
        conditions.append(Incident.reporter_id == criteria.reporter_id)
    return conditions

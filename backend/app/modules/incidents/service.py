from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident, IncidentEvent
from app.modules.incidents.repository import IncidentChanges, IncidentFilter, IncidentOrder, IncidentRepository
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import BusinessRuleError, ConflictError, NotFoundError, PermissionDeniedError

CENTRAL_ROLES = frozenset({UserRole.ANALYST, UserRole.SUPERVISOR})

CONFLICT_MESSAGE = "Este incidente foi alterado por outra pessoa. Confira o estado atual."
NOT_FOUND_MESSAGE = "Incidente não encontrado."

ALLOWED_TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    IncidentStatus.OPEN: frozenset({IncidentStatus.INVESTIGATING}),
    IncidentStatus.INVESTIGATING: frozenset({IncidentStatus.CLOSED, IncidentStatus.INCONCLUSIVE, IncidentStatus.OPEN}),
    IncidentStatus.CLOSED: frozenset(),
    IncidentStatus.INCONCLUSIVE: frozenset(),
}

FINAL_STATUSES = frozenset(status for status, targets in ALLOWED_TRANSITIONS.items() if not targets)

SUGGESTED_CRITICALITY: dict[IncidentCategory, Criticality] = {
    IncidentCategory.ACCIDENT_WITH_VICTIMS: Criticality.HIGH,
    IncidentCategory.VEHICLE_ACCIDENT: Criticality.HIGH,
    IncidentCategory.ROAD_BLOCKAGE: Criticality.LOW,
    IncidentCategory.ADVERSE_WEATHER: Criticality.MEDIUM,
    IncidentCategory.MECHANICAL_PROBLEM: Criticality.MEDIUM,
}

FIXED_CRITICALITY_CATEGORIES = frozenset({IncidentCategory.ACCIDENT_WITH_VICTIMS})

STATUS_LABELS = {
    IncidentStatus.OPEN: "Aberto",
    IncidentStatus.INVESTIGATING: "Em Investigação",
    IncidentStatus.CLOSED: "Fechado",
    IncidentStatus.INCONCLUSIVE: "Inconclusivo",
}


@dataclass(frozen=True)
class IncidentReport:
    """Data a driver provides when reporting an incident. Without a criticality, the suggested one is used.

    The idempotency key identifies the report attempt, so retrying it does not create a second incident.
    """

    category: IncidentCategory
    location: str
    description: str
    idempotency_key: UUID
    criticality: Criticality | None = None


@dataclass(frozen=True)
class CategoryOption:
    """A category the driver can choose, with the criticality the form suggests for it."""

    category: IncidentCategory
    label: str
    suggested_criticality: Criticality
    criticality_locked: bool


def category_options() -> list[CategoryOption]:
    """Return every category with its suggested criticality, in declaration order."""
    return [
        CategoryOption(
            category=category,
            label=category.label,
            suggested_criticality=SUGGESTED_CRITICALITY[category],
            criticality_locked=category in FIXED_CRITICALITY_CATEGORIES,
        )
        for category in IncidentCategory
    ]


@dataclass(frozen=True)
class IncidentQueue:
    """Active incidents to show, plus how many active incidents exist of each criticality."""

    items: list[Incident]
    counts: dict[Criticality, int]


@dataclass(frozen=True)
class IncidentPage:
    """One page of incidents, plus how many incidents match in total."""

    items: list[Incident]
    total: int
    page: int
    page_size: int


class IncidentService:
    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def get(self, incident_id: int) -> Incident:
        incident = self._repository.get(incident_id)
        if incident is None:
            raise NotFoundError(NOT_FOUND_MESSAGE)
        return incident

    def get_visible_to(self, incident_id: int, viewer: User) -> Incident:
        """Return the incident if `viewer` may see it: the central sees all, a driver only the ones they reported."""
        incident = self.get(incident_id)
        if viewer.role not in CENTRAL_ROLES and incident.reporter_id != viewer.id:
            # Same answer as a missing incident, so drivers cannot find out which ids exist.
            raise NotFoundError(NOT_FOUND_MESSAGE)
        return incident

    def list_active(
        self,
        criticalities: Collection[Criticality] = (),
        categories: Collection[IncidentCategory] = (),
        assignee_id: int | None = None,
        unassigned: bool = False,
    ) -> IncidentQueue:
        """Return the operational queue, most critical first and oldest first within the same criticality.

        An empty filter means no filter, and so does no assignee. `unassigned` keeps only the incidents
        nobody has taken. Counts ignore the filters, so the central always sees how many active
        incidents exist of each criticality.
        """
        active = self._repository.search(IncidentFilter(statuses=[status for status in IncidentStatus if status.is_active]))
        counts = {criticality: 0 for criticality in Criticality}
        for incident in active:
            counts[incident.criticality] += 1

        selected = [
            incident
            for incident in active
            if (not criticalities or incident.criticality in criticalities)
            and (not categories or incident.category in categories)
            and (assignee_id is None or incident.assignee_id == assignee_id)
            and (not unassigned or incident.assignee_id is None)
        ]
        return IncidentQueue(items=sorted(selected, key=lambda incident: incident.criticality.priority), counts=counts)

    def list_closed(
        self,
        page: int,
        page_size: int,
        statuses: Collection[IncidentStatus] = (),
        criticalities: Collection[Criticality] = (),
        categories: Collection[IncidentCategory] = (),
    ) -> IncidentPage:
        """Return one page of the history: closed and inconclusive incidents, from the most recently closed.

        An empty filter means no filter. Asking for an active status is refused instead of ignored,
        so a filter never silently turns into "everything".
        """
        if not set(statuses) <= FINAL_STATUSES:
            raise BusinessRuleError("O histórico mostra apenas incidentes encerrados.")

        criteria = IncidentFilter(
            statuses=statuses or FINAL_STATUSES,
            criticalities=criticalities,
            categories=categories,
            order=IncidentOrder.RECENTLY_CLOSED_FIRST,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return IncidentPage(items=self._repository.search(criteria), total=self._repository.count(criteria), page=page, page_size=page_size)

    def list_reported_by(self, reporter: User) -> list[Incident]:
        """Return every incident `reporter` reported, in any status, from the newest to the oldest."""
        return self._repository.search(IncidentFilter(reporter_id=reporter.id, order=IncidentOrder.NEWEST_FIRST))

    def report(self, reporter: User, report: IncidentReport) -> Incident:
        """Register a new incident reported by a driver. It starts open and without an assignee.

        Repeating a report with the same idempotency key returns the incident created the first time,
        without logging the report again.
        """
        incident = Incident(
            category=report.category,
            criticality=self._resolve_criticality(report.category, report.criticality),
            status=IncidentStatus.OPEN,
            location=report.location,
            description=report.description,
            reporter_id=reporter.id,
            idempotency_key=report.idempotency_key,
        )
        saved = self._repository.add(incident)
        if saved is incident:
            self._log(saved, reporter, from_status=None)
        return saved

    def assume(self, incident_id: int, actor: User, expected_version: int) -> Incident:
        """Make `actor` responsible for an open incident."""
        incident = self.get(incident_id)
        self._ensure_unchanged(incident, expected_version)
        if incident.status is not IncidentStatus.OPEN or incident.assignee_id is not None:
            raise BusinessRuleError("Apenas incidentes abertos e sem responsável podem ser assumidos.")

        assumed = self._save(incident_id, expected_version, {"status": IncidentStatus.INVESTIGATING, "assignee_id": actor.id})
        self._log(assumed, actor, from_status=IncidentStatus.OPEN)
        return assumed

    def change_status(
        self,
        incident_id: int,
        actor: User,
        expected_version: int,
        target: IncidentStatus,
        reason: str | None = None,
    ) -> Incident:
        """Move an incident under investigation to another status.

        Closing it (closed or inconclusive) requires a reason, and returning it to the
        queue removes its assignee so that anyone can assume it again, optionally with a reason.
        """
        incident = self.get(incident_id)
        self._ensure_unchanged(incident, expected_version)
        self._ensure_can_change_status(incident, actor)

        if incident.status is IncidentStatus.OPEN:
            raise BusinessRuleError("Para iniciar a investigação, assuma o incidente.")
        if target not in ALLOWED_TRANSITIONS[incident.status]:
            raise BusinessRuleError(
                f"Não é possível alterar um incidente de {STATUS_LABELS[incident.status]} para {STATUS_LABELS[target]}."
            )

        reason = reason.strip() if reason is not None else ""
        changes: IncidentChanges = {"status": target}
        if target is IncidentStatus.OPEN:
            changes["assignee_id"] = None
        if target in FINAL_STATUSES:
            if not reason:
                raise BusinessRuleError("Informe o motivo do encerramento.")
            changes |= {"closed_by_id": actor.id, "closed_at": datetime.now(UTC), "closure_reason": reason}

        # Read before saving: the saved incident is the same object, already in its new status.
        previous_status = incident.status
        updated = self._save(incident_id, expected_version, changes)
        self._log(updated, actor, from_status=previous_status, reason=reason or None)
        return updated

    def _resolve_criticality(self, category: IncidentCategory, chosen: Criticality | None) -> Criticality:
        suggested = SUGGESTED_CRITICALITY[category]
        if category in FIXED_CRITICALITY_CATEGORIES and chosen not in {None, suggested}:
            raise BusinessRuleError("Acidentes com vítimas são sempre de criticidade alta.")
        return chosen or suggested

    def _ensure_can_change_status(self, incident: Incident, actor: User) -> None:
        is_supervisor = actor.role is UserRole.SUPERVISOR
        is_assignee = actor.role is UserRole.ANALYST and incident.assignee_id == actor.id
        if not (is_supervisor or is_assignee):
            raise PermissionDeniedError("Apenas o responsável pelo incidente ou um supervisor pode alterar seu status.")

    def _ensure_unchanged(self, incident: Incident, expected_version: int) -> None:
        if incident.version != expected_version:
            raise ConflictError(CONFLICT_MESSAGE, current=incident)

    def _log(self, incident: Incident, actor: User, from_status: IncidentStatus | None, reason: str | None = None) -> None:
        """Add the change just made to the incident's change log (RN-12)."""
        event = IncidentEvent(incident=incident, actor_id=actor.id, from_status=from_status, to_status=incident.status, reason=reason)
        self._repository.add_event(event)

    def _save(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident:
        """Persist `changes`, failing with a conflict if someone else changed the incident in the meantime."""
        updated = self._repository.update_if_version(incident_id, expected_version, changes)
        if updated is None:
            raise ConflictError(CONFLICT_MESSAGE, current=self.get(incident_id))
        return updated

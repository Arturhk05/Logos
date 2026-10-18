from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges, IncidentRepository
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
    IncidentCategory.ROAD_BLOCKAGE: Criticality.MEDIUM,
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
    """Data a driver provides when reporting an incident. Without a criticality, the suggested one is used."""

    category: IncidentCategory
    location: str
    description: str
    criticality: Criticality | None = None


@dataclass(frozen=True)
class IncidentQueue:
    """Active incidents to show, plus how many active incidents exist of each criticality."""

    items: list[Incident]
    counts: dict[Criticality, int]


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
    ) -> IncidentQueue:
        """Return the operational queue, most critical first and oldest first within the same criticality.

        An empty filter means no filter. Counts ignore the filters, so the central always sees
        how many active incidents exist of each criticality.
        """
        active = self._repository.list_by_status([status for status in IncidentStatus if status.is_active])
        counts = {criticality: 0 for criticality in Criticality}
        for incident in active:
            counts[incident.criticality] += 1

        selected = [
            incident
            for incident in active
            if (not criticalities or incident.criticality in criticalities) and (not categories or incident.category in categories)
        ]
        return IncidentQueue(items=sorted(selected, key=lambda incident: incident.criticality.priority), counts=counts)

    def report(self, reporter: User, report: IncidentReport) -> Incident:
        """Register a new incident reported by a driver. It starts open and without an assignee."""
        if reporter.role is not UserRole.DRIVER:
            raise PermissionDeniedError("Apenas motoristas podem reportar incidentes.")

        incident = Incident(
            category=report.category,
            criticality=self._resolve_criticality(report.category, report.criticality),
            status=IncidentStatus.OPEN,
            location=report.location,
            description=report.description,
            reporter_id=reporter.id,
        )
        return self._repository.add(incident)

    def assume(self, incident_id: int, actor: User, expected_version: int) -> Incident:
        """Make `actor` responsible for an open incident."""
        if actor.role not in CENTRAL_ROLES:
            raise PermissionDeniedError("Apenas analistas e supervisores podem assumir incidentes.")

        incident = self.get(incident_id)
        self._ensure_unchanged(incident, expected_version)
        if incident.status is not IncidentStatus.OPEN or incident.assignee_id is not None:
            raise BusinessRuleError("Apenas incidentes abertos e sem responsável podem ser assumidos.")

        return self._save(incident_id, expected_version, {"status": IncidentStatus.INVESTIGATING, "assignee_id": actor.id})

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
        queue removes its assignee so that anyone can assume it again.
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

        changes: IncidentChanges = {"status": target}
        if target is IncidentStatus.OPEN:
            changes["assignee_id"] = None
        if target in FINAL_STATUSES:
            if reason is None or not reason.strip():
                raise BusinessRuleError("Informe o motivo do encerramento.")
            changes |= {"closed_by_id": actor.id, "closed_at": datetime.now(UTC), "closure_reason": reason.strip()}

        return self._save(incident_id, expected_version, changes)

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

    def _save(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident:
        """Persist `changes`, failing with a conflict if someone else changed the incident in the meantime."""
        updated = self._repository.update_if_version(incident_id, expected_version, changes)
        if updated is None:
            raise ConflictError(CONFLICT_MESSAGE, current=self.get(incident_id))
        return updated

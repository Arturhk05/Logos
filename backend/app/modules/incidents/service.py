from datetime import UTC, datetime

from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges, IncidentRepository
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import BusinessRuleError, ConflictError, NotFoundError, PermissionDeniedError

CENTRAL_ROLES = frozenset({UserRole.ANALYST, UserRole.SUPERVISOR})

CONFLICT_MESSAGE = "Este incidente foi alterado por outra pessoa. Confira o estado atual."

ALLOWED_TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    IncidentStatus.OPEN: frozenset({IncidentStatus.INVESTIGATING}),
    IncidentStatus.INVESTIGATING: frozenset({IncidentStatus.CLOSED, IncidentStatus.INCONCLUSIVE, IncidentStatus.OPEN}),
    IncidentStatus.CLOSED: frozenset(),
    IncidentStatus.INCONCLUSIVE: frozenset(),
}

FINAL_STATUSES = frozenset(status for status, targets in ALLOWED_TRANSITIONS.items() if not targets)

STATUS_LABELS = {
    IncidentStatus.OPEN: "Aberto",
    IncidentStatus.INVESTIGATING: "Em Investigação",
    IncidentStatus.CLOSED: "Fechado",
    IncidentStatus.INCONCLUSIVE: "Inconclusivo",
}


class IncidentService:
    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def get(self, incident_id: int) -> Incident:
        incident = self._repository.get(incident_id)
        if incident is None:
            raise NotFoundError("Incidente não encontrado.")
        return incident

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

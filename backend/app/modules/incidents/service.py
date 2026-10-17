from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges, IncidentRepository
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import BusinessRuleError, ConflictError, NotFoundError, PermissionDeniedError

CENTRAL_ROLES = frozenset({UserRole.ANALYST, UserRole.SUPERVISOR})

CONFLICT_MESSAGE = "Este incidente foi alterado por outra pessoa. Confira o estado atual."


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

    def _ensure_unchanged(self, incident: Incident, expected_version: int) -> None:
        if incident.version != expected_version:
            raise ConflictError(CONFLICT_MESSAGE, current=incident)

    def _save(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident:
        """Persist `changes`, failing with a conflict if someone else changed the incident in the meantime."""
        updated = self._repository.update_if_version(incident_id, expected_version, changes)
        if updated is None:
            raise ConflictError(CONFLICT_MESSAGE, current=self.get(incident_id))
        return updated

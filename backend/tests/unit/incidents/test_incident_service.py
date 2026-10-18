from datetime import UTC, datetime
from itertools import product

import pytest

from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges
from app.modules.incidents.service import IncidentService
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import BusinessRuleError, ConflictError, NotFoundError, PermissionDeniedError
from tests.factories import build_incident, build_user
from tests.fakes import InMemoryIncidentRepository


@pytest.fixture
def driver() -> User:
    return build_user(UserRole.DRIVER)


@pytest.fixture
def analyst() -> User:
    return build_user(UserRole.ANALYST)


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.SUPERVISOR])
def test_central_user_assumes_open_incident(driver: User, role: UserRole) -> None:
    actor = build_user(role)
    incident = build_incident(driver)
    service = IncidentService(InMemoryIncidentRepository(incident))

    assumed = service.assume(incident.id, actor, expected_version=1)

    assert assumed.status is IncidentStatus.INVESTIGATING
    assert assumed.assignee_id == actor.id
    assert assumed.version == 2


def test_driver_cannot_assume_incident(driver: User) -> None:
    incident = build_incident(driver)
    service = IncidentService(InMemoryIncidentRepository(incident))

    with pytest.raises(PermissionDeniedError):
        service.assume(incident.id, driver, expected_version=1)


def test_cannot_assume_incident_that_already_has_an_assignee(driver: User, analyst: User) -> None:
    incident = build_incident(driver, status=IncidentStatus.INVESTIGATING, assignee_id=analyst.id)
    service = IncidentService(InMemoryIncidentRepository(incident))

    with pytest.raises(BusinessRuleError):
        service.assume(incident.id, build_user(UserRole.ANALYST), expected_version=1)


def test_assume_with_outdated_version_raises_conflict_with_current_state(driver: User, analyst: User) -> None:
    incident = build_incident(driver)
    service = IncidentService(InMemoryIncidentRepository(incident))
    service.assume(incident.id, analyst, expected_version=1)

    with pytest.raises(ConflictError) as error:
        service.assume(incident.id, build_user(UserRole.ANALYST), expected_version=1)

    assert error.value.current.assignee_id == analyst.id


def test_assume_missing_incident_raises_not_found(analyst: User) -> None:
    service = IncidentService(InMemoryIncidentRepository())

    with pytest.raises(NotFoundError):
        service.assume(999, analyst, expected_version=1)


class RepositoryWhereAnotherAnalystWinsTheRace(InMemoryIncidentRepository):
    """Simulates another request assuming the incident between our read and our write."""

    def __init__(self, incident: Incident, winner: User) -> None:
        super().__init__(incident)
        self._winner = winner

    def update_if_version(self, incident_id: int, expected_version: int, changes: IncidentChanges) -> Incident | None:
        super().update_if_version(incident_id, expected_version, {"status": IncidentStatus.INVESTIGATING, "assignee_id": self._winner.id})
        return super().update_if_version(incident_id, expected_version, changes)


def test_losing_a_simultaneous_assume_raises_conflict_with_the_winner(driver: User, analyst: User) -> None:
    winner = build_user(UserRole.ANALYST)
    incident = build_incident(driver)
    service = IncidentService(RepositoryWhereAnotherAnalystWinsTheRace(incident, winner))

    with pytest.raises(ConflictError) as error:
        service.assume(incident.id, analyst, expected_version=1)

    assert error.value.current.assignee_id == winner.id


# --- change_status -----------------------------------------------------------

OPEN = IncidentStatus.OPEN
INVESTIGATING = IncidentStatus.INVESTIGATING
CLOSED = IncidentStatus.CLOSED
INCONCLUSIVE = IncidentStatus.INCONCLUSIVE

# Expected lifecycle, written independently from the implementation.
# OPEN -> INVESTIGATING is only possible through `assume`.
CHANGE_STATUS_TRANSITIONS = {
    (INVESTIGATING, CLOSED),
    (INVESTIGATING, INCONCLUSIVE),
    (INVESTIGATING, OPEN),
}


def build_incident_in(status: IncidentStatus, reporter: User, assignee: User) -> Incident:
    if status is OPEN:
        return build_incident(reporter)
    fields: dict[str, object] = {"status": status, "assignee_id": assignee.id}
    if status in {CLOSED, INCONCLUSIVE}:
        fields |= {"closed_by_id": assignee.id, "closed_at": datetime.now(UTC), "closure_reason": "Encerrado"}
    return build_incident(reporter, **fields)


@pytest.mark.parametrize(("current", "target"), list(product(IncidentStatus, repeat=2)))
def test_change_status_follows_the_incident_lifecycle(driver: User, analyst: User, current: IncidentStatus, target: IncidentStatus) -> None:
    supervisor = build_user(UserRole.SUPERVISOR)
    incident = build_incident_in(current, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))

    if (current, target) in CHANGE_STATUS_TRANSITIONS:
        updated = service.change_status(incident.id, supervisor, expected_version=1, target=target, reason="Motivo")
        assert updated.status is target
    else:
        with pytest.raises(BusinessRuleError):
            service.change_status(incident.id, supervisor, expected_version=1, target=target, reason="Motivo")


@pytest.mark.parametrize("final_status", [CLOSED, INCONCLUSIVE])
def test_assignee_closes_incident_recording_who_when_and_why(driver: User, analyst: User, final_status: IncidentStatus) -> None:
    incident = build_incident_in(INVESTIGATING, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))

    closed = service.change_status(incident.id, analyst, expected_version=1, target=final_status, reason="  Pneu trocado  ")

    assert closed.status is final_status
    assert closed.closed_by_id == analyst.id
    assert closed.closed_at is not None
    assert closed.closed_at.tzinfo is not None
    assert closed.closure_reason == "Pneu trocado"
    assert closed.version == 2


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_closing_requires_a_reason(driver: User, analyst: User, reason: str | None) -> None:
    incident = build_incident_in(INVESTIGATING, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))

    with pytest.raises(BusinessRuleError, match="motivo"):
        service.change_status(incident.id, analyst, expected_version=1, target=CLOSED, reason=reason)


def test_returning_to_the_queue_removes_the_assignee(driver: User, analyst: User) -> None:
    incident = build_incident_in(INVESTIGATING, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))

    returned = service.change_status(incident.id, analyst, expected_version=1, target=OPEN)

    assert returned.status is OPEN
    assert returned.assignee_id is None


def test_supervisor_changes_status_of_another_analysts_incident(driver: User, analyst: User) -> None:
    supervisor = build_user(UserRole.SUPERVISOR)
    incident = build_incident_in(INVESTIGATING, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))

    closed = service.change_status(incident.id, supervisor, expected_version=1, target=CLOSED, reason="Liberado pela supervisão")

    assert closed.status is CLOSED
    assert closed.closed_by_id == supervisor.id


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.DRIVER])
def test_only_assignee_or_supervisor_can_change_status(driver: User, analyst: User, role: UserRole) -> None:
    outsider = build_user(role)
    incident = build_incident_in(INVESTIGATING, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))

    with pytest.raises(PermissionDeniedError):
        service.change_status(incident.id, outsider, expected_version=1, target=CLOSED, reason="Motivo")


def test_change_status_with_outdated_version_raises_conflict(driver: User, analyst: User) -> None:
    incident = build_incident_in(INVESTIGATING, driver, analyst)
    service = IncidentService(InMemoryIncidentRepository(incident))
    service.change_status(incident.id, analyst, expected_version=1, target=OPEN)

    with pytest.raises(ConflictError) as error:
        service.change_status(incident.id, analyst, expected_version=1, target=CLOSED, reason="Motivo")

    assert error.value.current.status is OPEN

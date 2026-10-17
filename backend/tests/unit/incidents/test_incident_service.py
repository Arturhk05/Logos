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

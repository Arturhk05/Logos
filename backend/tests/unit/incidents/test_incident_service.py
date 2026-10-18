from datetime import UTC, datetime
from itertools import product
from uuid import UUID, uuid4

import pytest

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import IncidentChanges
from app.modules.incidents.service import SUGGESTED_CRITICALITY, IncidentReport, IncidentService, category_options
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


def test_only_assignee_or_supervisor_can_change_status(driver: User, analyst: User) -> None:
    outsider = build_user(UserRole.ANALYST)
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


# --- report ------------------------------------------------------------------


def build_report(
    category: IncidentCategory = IncidentCategory.MECHANICAL_PROBLEM,
    criticality: Criticality | None = None,
    idempotency_key: UUID | None = None,
) -> IncidentReport:
    return IncidentReport(
        category=category,
        location="BR-116, km 230",
        description="Pneu furado no acostamento",
        idempotency_key=idempotency_key or uuid4(),
        criticality=criticality,
    )


def test_driver_reports_incident_that_starts_open_without_assignee(driver: User) -> None:
    service = IncidentService(InMemoryIncidentRepository())

    incident = service.report(driver, build_report())

    assert incident.id is not None
    assert incident.status is IncidentStatus.OPEN
    assert incident.assignee_id is None
    assert incident.reporter_id == driver.id
    assert incident.location == "BR-116, km 230"
    assert incident.version == 1


@pytest.mark.parametrize(
    ("category", "suggested"),
    [
        (IncidentCategory.ACCIDENT_WITH_VICTIMS, Criticality.HIGH),
        (IncidentCategory.VEHICLE_ACCIDENT, Criticality.HIGH),
        (IncidentCategory.ROAD_BLOCKAGE, Criticality.MEDIUM),
        (IncidentCategory.ADVERSE_WEATHER, Criticality.MEDIUM),
        (IncidentCategory.MECHANICAL_PROBLEM, Criticality.MEDIUM),
    ],
)
def test_report_without_criticality_uses_the_suggestion_for_the_category(
    driver: User, category: IncidentCategory, suggested: Criticality
) -> None:
    service = IncidentService(InMemoryIncidentRepository())

    incident = service.report(driver, build_report(category))

    assert incident.criticality is suggested


def test_every_category_has_a_suggested_criticality() -> None:
    assert set(SUGGESTED_CRITICALITY) == set(IncidentCategory)


def test_driver_can_override_the_suggested_criticality(driver: User) -> None:
    service = IncidentService(InMemoryIncidentRepository())

    incident = service.report(driver, build_report(IncidentCategory.MECHANICAL_PROBLEM, Criticality.HIGH))

    assert incident.criticality is Criticality.HIGH


@pytest.mark.parametrize("criticality", [Criticality.MEDIUM, Criticality.LOW])
def test_accident_with_victims_cannot_be_reported_below_high(driver: User, criticality: Criticality) -> None:
    service = IncidentService(InMemoryIncidentRepository())

    with pytest.raises(BusinessRuleError):
        service.report(driver, build_report(IncidentCategory.ACCIDENT_WITH_VICTIMS, criticality))


def test_accident_with_victims_accepts_high_criticality(driver: User) -> None:
    service = IncidentService(InMemoryIncidentRepository())

    incident = service.report(driver, build_report(IncidentCategory.ACCIDENT_WITH_VICTIMS, Criticality.HIGH))

    assert incident.criticality is Criticality.HIGH


def test_reporting_twice_with_the_same_key_returns_the_first_incident(driver: User) -> None:
    service = IncidentService(InMemoryIncidentRepository())
    key = uuid4()
    first = service.report(driver, build_report(idempotency_key=key))

    second = service.report(driver, build_report(idempotency_key=key))

    assert second is first


def test_same_key_from_another_driver_creates_another_incident(driver: User) -> None:
    service = IncidentService(InMemoryIncidentRepository())
    other_driver = build_user(UserRole.DRIVER)
    key = uuid4()
    first = service.report(driver, build_report(idempotency_key=key))

    other = service.report(other_driver, build_report(idempotency_key=key))

    assert other.id != first.id
    assert other.reporter_id == other_driver.id


def _at(hour: int) -> datetime:
    return datetime(2026, 10, 18, hour, tzinfo=UTC)


def test_queue_orders_by_criticality_then_oldest_first(driver: User) -> None:
    low_08 = build_incident(driver, criticality=Criticality.LOW, created_at=_at(8))
    high_10 = build_incident(driver, criticality=Criticality.HIGH, created_at=_at(10))
    medium_07 = build_incident(driver, criticality=Criticality.MEDIUM, created_at=_at(7))
    high_09 = build_incident(driver, criticality=Criticality.HIGH, created_at=_at(9))
    medium_11 = build_incident(driver, criticality=Criticality.MEDIUM, created_at=_at(11))
    service = IncidentService(InMemoryIncidentRepository(low_08, high_10, medium_07, high_09, medium_11))

    queue = service.list_active()

    assert queue.items == [high_09, high_10, medium_07, medium_11, low_08]


def test_queue_excludes_closed_and_inconclusive(driver: User) -> None:
    open_incident = build_incident(driver, criticality=Criticality.HIGH, status=OPEN, created_at=_at(8))
    investigating = build_incident(driver, criticality=Criticality.HIGH, status=INVESTIGATING, created_at=_at(9))
    closed = build_incident(driver, criticality=Criticality.HIGH, status=CLOSED, created_at=_at(7))
    inconclusive = build_incident(driver, criticality=Criticality.HIGH, status=INCONCLUSIVE, created_at=_at(6))
    service = IncidentService(InMemoryIncidentRepository(open_incident, investigating, closed, inconclusive))

    assert service.list_active().items == [open_incident, investigating]
    assert service.list_active(criticalities={Criticality.HIGH}).items == [open_incident, investigating]


def test_queue_filters_by_several_criticalities(driver: User) -> None:
    high = build_incident(driver, criticality=Criticality.HIGH, created_at=_at(8))
    medium = build_incident(driver, criticality=Criticality.MEDIUM, created_at=_at(9))
    low = build_incident(driver, criticality=Criticality.LOW, created_at=_at(10))
    service = IncidentService(InMemoryIncidentRepository(high, medium, low))

    assert service.list_active(criticalities={Criticality.HIGH, Criticality.LOW}).items == [high, low]


def test_queue_filters_by_several_categories(driver: User) -> None:
    blockage = build_incident(driver, category=IncidentCategory.ROAD_BLOCKAGE, created_at=_at(8))
    weather = build_incident(driver, category=IncidentCategory.ADVERSE_WEATHER, created_at=_at(9))
    mechanical = build_incident(driver, category=IncidentCategory.MECHANICAL_PROBLEM, created_at=_at(10))
    service = IncidentService(InMemoryIncidentRepository(blockage, weather, mechanical))

    queue = service.list_active(categories={IncidentCategory.ROAD_BLOCKAGE, IncidentCategory.MECHANICAL_PROBLEM})

    assert queue.items == [blockage, mechanical]


def test_queue_combines_criticality_and_category_filters(driver: User) -> None:
    high_blockage = build_incident(driver, criticality=Criticality.HIGH, category=IncidentCategory.ROAD_BLOCKAGE, created_at=_at(8))
    low_blockage = build_incident(driver, criticality=Criticality.LOW, category=IncidentCategory.ROAD_BLOCKAGE, created_at=_at(9))
    high_weather = build_incident(driver, criticality=Criticality.HIGH, category=IncidentCategory.ADVERSE_WEATHER, created_at=_at(10))
    service = IncidentService(InMemoryIncidentRepository(high_blockage, low_blockage, high_weather))

    queue = service.list_active(criticalities={Criticality.HIGH}, categories={IncidentCategory.ROAD_BLOCKAGE})

    assert queue.items == [high_blockage]


def test_queue_counts_ignore_filters(driver: User) -> None:
    incidents = [
        build_incident(driver, criticality=Criticality.HIGH, created_at=_at(8)),
        build_incident(driver, criticality=Criticality.HIGH, created_at=_at(9)),
        build_incident(driver, criticality=Criticality.LOW, created_at=_at(10)),
        build_incident(driver, criticality=Criticality.HIGH, status=CLOSED, created_at=_at(7)),
    ]
    service = IncidentService(InMemoryIncidentRepository(*incidents))

    queue = service.list_active(criticalities={Criticality.LOW})

    assert len(queue.items) == 1
    assert queue.counts == {Criticality.HIGH: 2, Criticality.MEDIUM: 0, Criticality.LOW: 1}


def test_queue_counts_include_every_criticality_even_when_zero() -> None:
    queue = IncidentService(InMemoryIncidentRepository()).list_active()

    assert queue.items == []
    assert queue.counts == {Criticality.HIGH: 0, Criticality.MEDIUM: 0, Criticality.LOW: 0}


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.SUPERVISOR])
def test_central_user_sees_any_incident(driver: User, role: UserRole) -> None:
    incident = build_incident(driver)
    service = IncidentService(InMemoryIncidentRepository(incident))

    assert service.get_visible_to(incident.id, build_user(role)) is incident


def test_driver_sees_own_incident(driver: User) -> None:
    incident = build_incident(driver)
    service = IncidentService(InMemoryIncidentRepository(incident))

    assert service.get_visible_to(incident.id, driver) is incident


def test_driver_cannot_see_incident_of_another_driver(driver: User) -> None:
    incident = build_incident(driver)
    service = IncidentService(InMemoryIncidentRepository(incident))

    with pytest.raises(NotFoundError) as error:
        service.get_visible_to(incident.id, build_user(UserRole.DRIVER))

    assert error.value.message == "Incidente não encontrado."


def test_visible_incident_that_does_not_exist_is_not_found(analyst: User) -> None:
    with pytest.raises(NotFoundError):
        IncidentService(InMemoryIncidentRepository()).get_visible_to(999, analyst)


def test_driver_lists_own_incidents_newest_first(driver: User) -> None:
    closed_at_8 = build_incident(driver, status=CLOSED, created_at=_at(8))
    at_10 = build_incident(driver, created_at=_at(10))
    at_9 = build_incident(driver, created_at=_at(9))
    from_another_driver = build_incident(build_user(UserRole.DRIVER), created_at=_at(11))
    service = IncidentService(InMemoryIncidentRepository(closed_at_8, at_10, at_9, from_another_driver))

    assert service.list_reported_by(driver) == [at_10, at_9, closed_at_8]


# --- history -----------------------------------------------------------------


def build_closed(reporter: User, closed_at_hour: int, status: IncidentStatus = CLOSED, **overrides: object) -> Incident:
    fields: dict[str, object] = {"status": status, "closed_at": _at(closed_at_hour), "closure_reason": "Resolvido", "created_at": _at(1)}
    return build_incident(reporter, **(fields | overrides))


def test_history_lists_only_closed_incidents_recently_closed_first(driver: User) -> None:
    closed_at_10 = build_closed(driver, 10)
    inconclusive_at_11 = build_closed(driver, 11, INCONCLUSIVE)
    still_open = build_incident(driver, created_at=_at(12))
    service = IncidentService(InMemoryIncidentRepository(closed_at_10, inconclusive_at_11, still_open))

    page = service.list_closed(page=1, page_size=20)

    assert page.items == [inconclusive_at_11, closed_at_10]
    assert page.total == 2
    assert (page.page, page.page_size) == (1, 20)


def test_history_paginates(driver: User) -> None:
    oldest, middle, newest = build_closed(driver, 8), build_closed(driver, 9), build_closed(driver, 10)
    service = IncidentService(InMemoryIncidentRepository(oldest, middle, newest))

    page = service.list_closed(page=2, page_size=2)

    assert page.items == [oldest]
    assert page.total == 3


def test_history_page_past_the_end_is_empty(driver: User) -> None:
    service = IncidentService(InMemoryIncidentRepository(build_closed(driver, 8), build_closed(driver, 9)))

    page = service.list_closed(page=5, page_size=2)

    assert page.items == []
    assert page.total == 2


def test_history_filters_by_status_criticality_and_category(driver: User) -> None:
    expected = build_closed(driver, 8, INCONCLUSIVE, criticality=Criticality.HIGH, category=IncidentCategory.ROAD_BLOCKAGE)
    other_status = build_closed(driver, 9, CLOSED, criticality=Criticality.HIGH, category=IncidentCategory.ROAD_BLOCKAGE)
    other_criticality = build_closed(driver, 10, INCONCLUSIVE, criticality=Criticality.LOW, category=IncidentCategory.ROAD_BLOCKAGE)
    other_category = build_closed(driver, 11, INCONCLUSIVE, criticality=Criticality.HIGH, category=IncidentCategory.ADVERSE_WEATHER)
    service = IncidentService(InMemoryIncidentRepository(expected, other_status, other_criticality, other_category))

    page = service.list_closed(
        page=1,
        page_size=20,
        statuses={INCONCLUSIVE},
        criticalities={Criticality.HIGH},
        categories={IncidentCategory.ROAD_BLOCKAGE},
    )

    assert page.items == [expected]
    assert page.total == 1


@pytest.mark.parametrize("active_status", [OPEN, INVESTIGATING])
def test_history_with_active_status_is_rejected(driver: User, active_status: IncidentStatus) -> None:
    service = IncidentService(InMemoryIncidentRepository(build_closed(driver, 8)))

    with pytest.raises(BusinessRuleError, match="encerrados"):
        service.list_closed(page=1, page_size=20, statuses={CLOSED, active_status})


def test_history_puts_incidents_without_closing_time_last(driver: User) -> None:
    first_without_time = build_closed(driver, 8, closed_at=None)
    second_without_time = build_closed(driver, 8, closed_at=None)
    closed_at_9 = build_closed(driver, 9)
    service = IncidentService(InMemoryIncidentRepository(first_without_time, closed_at_9, second_without_time))

    page = service.list_closed(page=1, page_size=20)

    assert page.items == [closed_at_9, second_without_time, first_without_time]


# --- categories --------------------------------------------------------------


def test_only_accident_with_victims_has_locked_criticality() -> None:
    locked = {option.category for option in category_options() if option.criticality_locked}

    assert locked == {IncidentCategory.ACCIDENT_WITH_VICTIMS}

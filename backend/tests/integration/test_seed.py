from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.security import verify_password
from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from scripts.seed import reset_incidents, seed_incidents, seed_phones, seed_users
from tests.factories import create_incident, create_user

EXPECTED_USERS = {
    "camila": UserRole.ANALYST,
    "lucas": UserRole.ANALYST,
    "roberto": UserRole.SUPERVISOR,
    "jose": UserRole.DRIVER,
    "maria": UserRole.DRIVER,
    "antonio": UserRole.DRIVER,
    "paulo": UserRole.DRIVER,
}
# Fictitious numbers with area code 00, so no demo link opens a chat with a real person.
EXPECTED_PHONES = {
    "jose": "5500900000001",
    "maria": "5500900000002",
    "antonio": "5500900000003",
    "paulo": "5500900000004",
}
ACTIVE = {IncidentStatus.OPEN, IncidentStatus.INVESTIGATING}
CLOSED = {IncidentStatus.CLOSED, IncidentStatus.INCONCLUSIVE}


def _users(session: Session) -> list[User]:
    return list(session.scalars(select(User).where(User.username.in_(EXPECTED_USERS))))


def _seeded_incidents(session: Session) -> list[Incident]:
    seed_users(session)
    seed_incidents(session)
    return list(session.scalars(select(Incident)))


def test_seed_creates_one_login_per_demo_user(db_session: Session) -> None:
    seed_users(db_session)

    users = _users(db_session)
    assert {user.username: user.role for user in users} == EXPECTED_USERS
    assert all(verify_password("logos123", user.password_hash) for user in users)


def test_seed_usernames_are_normalized(db_session: Session) -> None:
    seed_users(db_session)

    usernames = db_session.scalars(select(User.username))
    assert all(username == username.strip().lower() for username in usernames)


def test_seed_can_run_twice(db_session: Session) -> None:
    assert seed_users(db_session) == len(EXPECTED_USERS)
    assert seed_users(db_session) == 0

    assert len(_users(db_session)) == len(EXPECTED_USERS)


def test_seed_gives_every_demo_driver_a_phone(db_session: Session) -> None:
    seed_users(db_session)
    seed_phones(db_session)

    phones = {user.username: user.phone for user in _users(db_session)}
    assert phones == EXPECTED_PHONES | {"camila": None, "lucas": None, "roberto": None}


def test_seed_fills_missing_phones_of_existing_users(db_session: Session) -> None:
    jose = create_user(db_session, UserRole.DRIVER, username="jose", phone=None)
    seed_users(db_session)

    assert seed_phones(db_session) == len(EXPECTED_PHONES)
    assert jose.phone == "5500900000001"
    assert seed_phones(db_session) == 0
    assert jose.phone == "5500900000001"


def test_seed_phones_keep_an_existing_phone(db_session: Session) -> None:
    jose = create_user(db_session, UserRole.DRIVER, username="jose", phone="5561999998888")
    seed_users(db_session)

    seed_phones(db_session)

    assert jose.phone == "5561999998888"


def test_seed_fills_the_queue_with_100_active_incidents_and_the_history_with_40(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)

    assert sum(incident.status in ACTIVE for incident in incidents) == 100
    assert sum(incident.status in CLOSED for incident in incidents) == 40


def test_seed_incidents_run_only_on_an_empty_table(db_session: Session) -> None:
    seed_users(db_session)
    assert seed_incidents(db_session) == 140
    assert seed_incidents(db_session) == 0

    assert len(list(db_session.scalars(select(Incident)))) == 140


def test_seed_incidents_keep_existing_incidents_untouched(db_session: Session) -> None:
    seed_users(db_session)
    create_incident(db_session, create_user(db_session, UserRole.DRIVER))

    assert seed_incidents(db_session) == 0


def test_seed_incidents_cover_every_status_category_and_criticality(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)
    active = [incident for incident in incidents if incident.status in ACTIVE]

    assert {incident.status for incident in incidents} == set(IncidentStatus)
    assert {incident.category for incident in active} == set(IncidentCategory)
    assert {incident.criticality for incident in active} == set(Criticality)


def test_seed_incidents_are_reported_by_several_drivers(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)
    drivers = {user.id for user in _users(db_session) if user.role is UserRole.DRIVER}

    reporters = {incident.reporter_id for incident in incidents}
    assert reporters == drivers


def test_seed_accidents_with_victims_are_always_high(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)

    victims = [incident for incident in incidents if incident.category is IncidentCategory.ACCIDENT_WITH_VICTIMS]
    assert victims
    assert all(incident.criticality is Criticality.HIGH for incident in victims)


def test_seed_open_incidents_have_no_assignee(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)

    open_incidents = [incident for incident in incidents if incident.status is IncidentStatus.OPEN]
    assert all(incident.assignee_id is None and incident.closed_by_id is None for incident in open_incidents)


def test_seed_handled_incidents_are_assigned_to_the_central(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)
    central = {user.id for user in _users(db_session) if user.role in {UserRole.ANALYST, UserRole.SUPERVISOR}}

    handled = [incident for incident in incidents if incident.status is not IncidentStatus.OPEN]
    assert all(incident.assignee_id in central for incident in handled)


def test_seed_closed_incidents_record_who_closed_when_and_why(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)
    central = {user.id for user in _users(db_session) if user.role in {UserRole.ANALYST, UserRole.SUPERVISOR}}

    for incident in incidents:
        if incident.status in CLOSED:
            assert incident.closed_by_id in central
            assert incident.closure_reason
            assert incident.closed_at is not None
            assert incident.created_at < incident.closed_at <= datetime.now(UTC)
        else:
            assert incident.closed_by_id is None
            assert incident.closed_at is None
            assert incident.closure_reason is None


def test_seed_incidents_were_opened_at_different_times_in_the_past(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)

    assert all(incident.created_at < datetime.now(UTC) for incident in incidents)
    assert len({incident.created_at for incident in incidents}) == len(incidents)


# --- change log (RN-12) ------------------------------------------------------


def test_seed_every_incident_starts_with_its_report(db_session: Session) -> None:
    for incident in _seeded_incidents(db_session):
        first = incident.events[0]
        assert (first.from_status, first.to_status, first.actor_id) == (None, IncidentStatus.OPEN, incident.reporter_id)
        assert first.created_at == incident.created_at


def test_seed_history_matches_the_current_state(db_session: Session) -> None:
    for incident in _seeded_incidents(db_session):
        last = incident.events[-1]
        assert last.to_status is incident.status
        assert last.created_at == incident.updated_at
        assert incident.version == len(incident.events)
        for previous, current in zip(incident.events, incident.events[1:], strict=False):
            assert current.from_status is previous.to_status


def test_seed_handled_incidents_were_assumed_by_their_assignee(db_session: Session) -> None:
    for incident in _seeded_incidents(db_session):
        if incident.status is not IncidentStatus.OPEN:
            assumed = [event for event in incident.events if event.to_status is IncidentStatus.INVESTIGATING]
            assert assumed[-1].actor_id == incident.assignee_id


def test_seed_closed_incidents_end_with_their_closing(db_session: Session) -> None:
    for incident in _seeded_incidents(db_session):
        if incident.status in CLOSED:
            last = incident.events[-1]
            assert (last.actor_id, last.created_at, last.reason) == (incident.closed_by_id, incident.closed_at, incident.closure_reason)


def test_seed_some_incidents_were_returned_to_the_queue_with_a_reason(db_session: Session) -> None:
    incidents = _seeded_incidents(db_session)
    supervisors = {user.id for user in _users(db_session) if user.role is UserRole.SUPERVISOR}
    returns = [
        event
        for incident in incidents
        for event in incident.events
        if (event.from_status, event.to_status) == (IncidentStatus.INVESTIGATING, IncidentStatus.OPEN)
    ]

    assert returns
    assert all(event.reason and event.actor_id in supervisors for event in returns)


def test_seed_events_are_in_chronological_order(db_session: Session) -> None:
    for incident in _seeded_incidents(db_session):
        moments = [event.created_at for event in incident.events]
        assert moments == sorted(moments)
        assert len(set(moments)) == len(moments)


def test_reset_incidents_recreates_the_sample_data(db_session: Session) -> None:
    seed_users(db_session)
    create_incident(db_session, create_user(db_session, UserRole.DRIVER), description="Criado à mão")
    seed_incidents(db_session)

    assert reset_incidents(db_session) == 1
    assert seed_incidents(db_session) == 140

    incidents = list(db_session.scalars(select(Incident)))
    assert len(incidents) == 140
    assert "Criado à mão" not in {incident.description for incident in incidents}

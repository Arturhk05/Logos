from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.security import verify_password
from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from scripts.seed import seed_incidents, seed_users
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

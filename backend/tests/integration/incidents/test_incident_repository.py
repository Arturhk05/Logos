from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier

from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.incidents.repository import SqlAlchemyIncidentRepository
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.factories import create_incident, create_user


def test_add_persists_incident_with_generated_fields(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER)
    incident = Incident(
        category=IncidentCategory.ROAD_BLOCKAGE,
        criticality=Criticality.MEDIUM,
        status=IncidentStatus.OPEN,
        location="BR-101, km 12",
        description="Pista bloqueada por queda de barreira",
        reporter_id=driver.id,
    )

    added = SqlAlchemyIncidentRepository(db_session).add(incident)

    assert added.id is not None
    assert added.version == 1
    assert added.created_at is not None
    assert SqlAlchemyIncidentRepository(db_session).get(added.id) is not None


def test_get_returns_none_for_missing_incident(db_session: Session) -> None:
    assert SqlAlchemyIncidentRepository(db_session).get(999_999) is None


def test_update_if_version_applies_changes_and_bumps_version(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER)
    analyst = create_user(db_session, UserRole.ANALYST)
    incident = create_incident(db_session, driver)

    updated = SqlAlchemyIncidentRepository(db_session).update_if_version(
        incident.id, expected_version=1, changes={"status": IncidentStatus.INVESTIGATING, "assignee_id": analyst.id}
    )

    assert updated is not None
    assert updated.status is IncidentStatus.INVESTIGATING
    assert updated.assignee_id == analyst.id
    assert updated.version == 2


def test_update_if_version_does_nothing_when_version_is_outdated(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER)
    analyst = create_user(db_session, UserRole.ANALYST)
    incident = create_incident(db_session, driver)
    repository = SqlAlchemyIncidentRepository(db_session)

    outdated = repository.update_if_version(
        incident.id, expected_version=7, changes={"status": IncidentStatus.INVESTIGATING, "assignee_id": analyst.id}
    )

    assert outdated is None
    current = repository.get(incident.id)
    assert current is not None
    assert current.status is IncidentStatus.OPEN
    assert current.version == 1


def test_only_one_of_many_simultaneous_updates_succeeds(database_engine: Engine) -> None:
    """Real concurrency: each analyst uses its own connection and transaction, like separate requests.

    All of them try to update version 1 at the same moment. Only the atomic version check
    in the UPDATE statement prevents more than one from succeeding.
    """
    analysts_count = 10

    with Session(database_engine, expire_on_commit=False) as setup:
        driver = create_user(setup, UserRole.DRIVER)
        analysts = [create_user(setup, UserRole.ANALYST) for _ in range(analysts_count)]
        incident = create_incident(setup, driver)
        setup.commit()

    start_together = Barrier(analysts_count, timeout=10)

    def try_to_assume(analyst: User) -> bool:
        with Session(database_engine) as session, session.begin():
            start_together.wait()
            updated = SqlAlchemyIncidentRepository(session).update_if_version(
                incident.id, expected_version=1, changes={"status": IncidentStatus.INVESTIGATING, "assignee_id": analyst.id}
            )
            return updated is not None

    try:
        with ThreadPoolExecutor(max_workers=analysts_count) as executor:
            outcomes = list(executor.map(try_to_assume, analysts))

        assert outcomes.count(True) == 1
    finally:
        with Session(database_engine) as cleanup, cleanup.begin():
            cleanup.execute(delete(Incident).where(Incident.id == incident.id))
            cleanup.execute(delete(User).where(User.id.in_([driver.id, *(analyst.id for analyst in analysts)])))


def test_list_by_status_returns_only_requested_statuses_from_oldest(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER)
    open_at_10 = create_incident(db_session, driver, status=IncidentStatus.OPEN, created_at=datetime(2026, 10, 18, 10, tzinfo=UTC))
    create_incident(db_session, driver, status=IncidentStatus.CLOSED, created_at=datetime(2026, 10, 18, 9, tzinfo=UTC))
    investigating_at_8 = create_incident(
        db_session, driver, status=IncidentStatus.INVESTIGATING, created_at=datetime(2026, 10, 18, 8, tzinfo=UTC)
    )
    open_at_11 = create_incident(db_session, driver, status=IncidentStatus.OPEN, created_at=datetime(2026, 10, 18, 11, tzinfo=UTC))

    listed = SqlAlchemyIncidentRepository(db_session).list_by_status({IncidentStatus.OPEN, IncidentStatus.INVESTIGATING})

    assert [incident.id for incident in listed] == [investigating_at_8.id, open_at_10.id, open_at_11.id]


def test_relationships_load_the_related_users(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER, username="jose")
    analyst = create_user(db_session, UserRole.ANALYST, username="camila")
    supervisor = create_user(db_session, UserRole.SUPERVISOR, username="roberto")
    incident = create_incident(
        db_session,
        driver,
        status=IncidentStatus.CLOSED,
        assignee_id=analyst.id,
        closed_by_id=supervisor.id,
        closed_at=datetime(2026, 10, 18, 12, tzinfo=UTC),
        closure_reason="Pista liberada",
    )

    assert incident.reporter.username == "jose"
    assert incident.assignee is not None
    assert incident.assignee.username == "camila"
    assert incident.closed_by is not None
    assert incident.closed_by.username == "roberto"


def test_update_if_version_refreshes_already_loaded_relationships(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER)
    first = create_user(db_session, UserRole.ANALYST, username="camila")
    second = create_user(db_session, UserRole.ANALYST, username="lucas")
    incident = create_incident(db_session, driver, status=IncidentStatus.INVESTIGATING, assignee_id=first.id)
    repository = SqlAlchemyIncidentRepository(db_session)
    loaded = repository.get(incident.id)
    assert loaded is not None
    assert loaded.assignee is not None
    assert loaded.assignee.username == "camila"

    updated = repository.update_if_version(incident.id, expected_version=1, changes={"assignee_id": second.id})

    assert updated is not None
    assert updated.assignee is not None
    assert updated.assignee.username == "lucas"


def test_list_by_status_breaks_ties_by_id(db_session: Session) -> None:
    driver = create_user(db_session, UserRole.DRIVER)
    same_time = datetime(2026, 10, 18, 10, tzinfo=UTC)
    first = create_incident(db_session, driver, created_at=same_time)
    second = create_incident(db_session, driver, created_at=same_time)

    listed = SqlAlchemyIncidentRepository(db_session).list_by_status({IncidentStatus.OPEN})

    assert [incident.id for incident in listed] == [first.id, second.id]

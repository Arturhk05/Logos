from concurrent.futures import ThreadPoolExecutor
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

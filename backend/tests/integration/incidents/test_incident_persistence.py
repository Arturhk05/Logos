from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident, IncidentEvent
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.factories import create_incident, create_user


@pytest.fixture
def driver(db_session: Session) -> User:
    user = User(username="jose", password_hash="not-a-real-hash", role=UserRole.DRIVER)
    db_session.add(user)
    db_session.flush()
    return user


def test_new_incident_starts_open_without_assignee_at_version_one(db_session: Session, driver: User) -> None:
    incident = Incident(
        category=IncidentCategory.MECHANICAL_PROBLEM,
        criticality=Criticality.MEDIUM,
        location="BR-116, km 230",
        description="Pneu furado no acostamento",
        reporter_id=driver.id,
    )
    db_session.add(incident)
    db_session.flush()
    db_session.refresh(incident)

    assert incident.status is IncidentStatus.OPEN
    assert incident.assignee_id is None
    assert incident.version == 1
    assert incident.created_at is not None


@pytest.mark.parametrize(
    ("column", "constraint"),
    [
        ("category", "ck_incidents_category_valid"),
        ("criticality", "ck_incidents_criticality_valid"),
        ("status", "ck_incidents_status_valid"),
    ],
)
def test_database_rejects_values_outside_the_enum(db_session: Session, driver: User, column: str, constraint: str) -> None:
    values = {
        "category": "MECHANICAL_PROBLEM",
        "criticality": "MEDIUM",
        "status": "OPEN",
        "location": "BR-116, km 230",
        "description": "Pneu furado",
        "reporter_id": driver.id,
    } | {column: "INVALID"}

    # Raw SQL bypasses the ORM enum handling, so only the database constraint can reject it.
    insert = text(
        "INSERT INTO incidents (category, criticality, status, location, description, reporter_id) "
        "VALUES (:category, :criticality, :status, :location, :description, :reporter_id)"
    )
    with pytest.raises(IntegrityError, match=constraint), db_session.begin_nested():
        db_session.execute(insert, values)


def test_incident_events_are_saved_with_their_actor(db_session: Session, driver: User) -> None:
    incident = create_incident(db_session, driver)
    db_session.add(IncidentEvent(incident=incident, actor_id=driver.id, from_status=None, to_status=IncidentStatus.OPEN))
    db_session.flush()
    db_session.expire_all()

    [event] = db_session.get_one(Incident, incident.id).events
    assert event.actor.username == "jose"
    assert event.from_status is None
    assert event.to_status is IncidentStatus.OPEN
    assert event.reason is None
    assert event.created_at is not None


def test_incident_events_are_listed_oldest_first(db_session: Session, driver: User) -> None:
    analyst = create_user(db_session, UserRole.ANALYST)
    incident = create_incident(db_session, driver)
    start = datetime(2026, 10, 19, 8, 0, tzinfo=UTC)
    db_session.add_all(
        [
            IncidentEvent(
                incident=incident,
                actor_id=analyst.id,
                from_status=IncidentStatus.OPEN,
                to_status=IncidentStatus.INVESTIGATING,
                created_at=start + timedelta(minutes=10),
            ),
            IncidentEvent(
                incident=incident,
                actor_id=analyst.id,
                from_status=IncidentStatus.INVESTIGATING,
                to_status=IncidentStatus.CLOSED,
                reason="Pista liberada",
                created_at=start + timedelta(minutes=30),
            ),
            IncidentEvent(incident=incident, actor_id=driver.id, from_status=None, to_status=IncidentStatus.OPEN, created_at=start),
        ]
    )
    db_session.flush()
    db_session.expire_all()

    events = db_session.get_one(Incident, incident.id).events
    assert [event.to_status for event in events] == [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, IncidentStatus.CLOSED]


@pytest.mark.parametrize(
    ("column", "constraint"),
    [
        ("from_status", "ck_incident_events_from_status_valid"),
        ("to_status", "ck_incident_events_to_status_valid"),
    ],
)
def test_database_rejects_event_statuses_outside_the_enum(db_session: Session, driver: User, column: str, constraint: str) -> None:
    incident = create_incident(db_session, driver)
    values = {"incident_id": incident.id, "actor_id": driver.id, "from_status": "OPEN", "to_status": "INVESTIGATING"} | {column: "REOPENED"}

    insert = text(
        "INSERT INTO incident_events (incident_id, actor_id, from_status, to_status) "
        "VALUES (:incident_id, :actor_id, :from_status, :to_status)"
    )
    with pytest.raises(IntegrityError, match=constraint), db_session.begin_nested():
        db_session.execute(insert, values)

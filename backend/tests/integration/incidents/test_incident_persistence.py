import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.users.enums import UserRole
from app.modules.users.models import User


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

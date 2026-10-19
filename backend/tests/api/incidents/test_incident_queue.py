from datetime import UTC, datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.users.enums import UserRole
from tests.api.conftest import LoginAs
from tests.factories import create_incident, create_user


def _at(hour: int) -> datetime:
    return datetime(2026, 10, 18, hour, tzinfo=UTC)


def test_queue_returns_active_incidents_in_priority_order_with_counts(
    db_client: TestClient, db_session: Session, login_as: LoginAs
) -> None:
    analyst = login_as(UserRole.ANALYST, "camila")
    driver = create_user(db_session, UserRole.DRIVER, username="jose")
    low = create_incident(
        db_session,
        driver,
        criticality=Criticality.LOW,
        category=IncidentCategory.ADVERSE_WEATHER,
        location="BR-116, km 10",
        created_at=_at(8),
    )
    high = create_incident(
        db_session,
        driver,
        criticality=Criticality.HIGH,
        category=IncidentCategory.VEHICLE_ACCIDENT,
        status=IncidentStatus.INVESTIGATING,
        assignee_id=analyst.id,
        location="BR-101, km 20",
        created_at=_at(9),
    )
    create_incident(db_session, driver, criticality=Criticality.HIGH, status=IncidentStatus.CLOSED, created_at=_at(7))

    response = db_client.get("/api/incidents")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "items": [
            {
                "id": high.id,
                "category": "VEHICLE_ACCIDENT",
                "criticality": "HIGH",
                "status": "INVESTIGATING",
                "location": "BR-101, km 20",
                "created_at": "2026-10-18T09:00:00Z",
                "assignee": {"id": analyst.id, "username": "camila"},
            },
            {
                "id": low.id,
                "category": "ADVERSE_WEATHER",
                "criticality": "LOW",
                "status": "OPEN",
                "location": "BR-116, km 10",
                "created_at": "2026-10-18T08:00:00Z",
                "assignee": None,
            },
        ],
        "counts": {"HIGH": 1, "MEDIUM": 0, "LOW": 1},
    }


def test_queue_applies_filters_from_the_query_string(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.SUPERVISOR, "roberto")
    driver = create_user(db_session, UserRole.DRIVER)
    high_blockage = create_incident(
        db_session, driver, criticality=Criticality.HIGH, category=IncidentCategory.ROAD_BLOCKAGE, created_at=_at(8)
    )
    low_blockage = create_incident(
        db_session, driver, criticality=Criticality.LOW, category=IncidentCategory.ROAD_BLOCKAGE, created_at=_at(9)
    )
    create_incident(db_session, driver, criticality=Criticality.MEDIUM, category=IncidentCategory.ROAD_BLOCKAGE, created_at=_at(10))
    create_incident(db_session, driver, criticality=Criticality.HIGH, category=IncidentCategory.ADVERSE_WEATHER, created_at=_at(11))

    response = db_client.get("/api/incidents?criticality=HIGH&criticality=LOW&category=ROAD_BLOCKAGE")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.json()["items"]] == [high_blockage.id, low_blockage.id]


def test_queue_with_invalid_filter_returns_422(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")

    response = db_client.get("/api/incidents?criticality=URGENTE")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Dados inválidos. Revise os campos e tente novamente."}


def test_driver_cannot_see_the_queue(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.get("/api/incidents")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Você não tem permissão para realizar esta ação."}


def test_queue_requires_login(db_client: TestClient) -> None:
    response = db_client.get("/api/incidents")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_queue_items_do_not_include_events(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")
    create_incident(db_session, create_user(db_session, UserRole.DRIVER))

    response = db_client.get("/api/incidents")

    [item] = response.json()["items"]
    assert "events" not in item

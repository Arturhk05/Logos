from datetime import UTC, datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.users.enums import UserRole
from tests.api.conftest import LoginAs
from tests.factories import create_incident, create_user


def _at(hour: int) -> datetime:
    return datetime(2026, 10, 18, hour, tzinfo=UTC)


def test_driver_sees_only_own_incidents_newest_first(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    jose = login_as(UserRole.DRIVER, "jose")
    camila = create_user(db_session, UserRole.ANALYST, username="camila")
    older = create_incident(db_session, jose, created_at=_at(8))
    assumed = create_incident(
        db_session,
        jose,
        category=IncidentCategory.ROAD_BLOCKAGE,
        criticality=Criticality.HIGH,
        status=IncidentStatus.INVESTIGATING,
        assignee_id=camila.id,
        location="BR-101, km 12",
        created_at=_at(9),
    )
    create_incident(db_session, create_user(db_session, UserRole.DRIVER), created_at=_at(10))

    response = db_client.get("/api/incidents/mine")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.json()] == [assumed.id, older.id]
    assert response.json()[0] == {
        "id": assumed.id,
        "category": "ROAD_BLOCKAGE",
        "criticality": "HIGH",
        "status": "INVESTIGATING",
        "location": "BR-101, km 12",
        "created_at": "2026-10-18T09:00:00Z",
        "assignee": {"id": camila.id, "username": "camila"},
    }


def test_driver_without_reports_gets_empty_list(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.get("/api/incidents/mine")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.SUPERVISOR])
def test_central_user_cannot_list_driver_incidents(db_client: TestClient, login_as: LoginAs, role: UserRole) -> None:
    login_as(role, "central")

    response = db_client.get("/api/incidents/mine")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Você não tem permissão para realizar esta ação."}


def test_my_incidents_requires_login(db_client: TestClient) -> None:
    response = db_client.get("/api/incidents/mine")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

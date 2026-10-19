import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.incidents.enums import IncidentStatus
from app.modules.users.enums import UserRole
from tests.api.conftest import LoginAs
from tests.factories import create_incident, create_user

CONFLICT_MESSAGE = "Este incidente foi alterado por outra pessoa. Confira o estado atual."
FORBIDDEN = {"detail": "Você não tem permissão para realizar esta ação."}


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.SUPERVISOR])
def test_central_user_assumes_open_incident(db_client: TestClient, db_session: Session, login_as: LoginAs, role: UserRole) -> None:
    user = login_as(role, "central")
    incident = create_incident(db_session, create_user(db_session, UserRole.DRIVER))

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "INVESTIGATING"
    assert response.json()["assignee"] == {"id": user.id, "username": "central"}
    assert response.json()["version"] == 2


def test_assume_with_outdated_version_returns_409_with_current_state(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")
    lucas = create_user(db_session, UserRole.ANALYST, username="lucas")
    incident = create_incident(
        db_session, create_user(db_session, UserRole.DRIVER), status=IncidentStatus.INVESTIGATING, assignee_id=lucas.id, version=2
    )

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == CONFLICT_MESSAGE
    assert response.json()["current"]["assignee"] == {"id": lucas.id, "username": "lucas"}
    assert response.json()["current"]["version"] == 2
    assert "password_hash" not in response.text


def test_conflict_response_includes_the_reporter_phone(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")
    lucas = create_user(db_session, UserRole.ANALYST, username="lucas")
    driver = create_user(db_session, UserRole.DRIVER, phone="5500900000001")
    incident = create_incident(db_session, driver, status=IncidentStatus.INVESTIGATING, assignee_id=lucas.id, version=2)

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_409_CONFLICT
    current = response.json()["current"]
    assert current["reporter"]["phone"] == "5500900000001"
    assert "phone" not in current["assignee"]


def test_assume_incident_that_has_an_assignee_returns_422(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")
    lucas = create_user(db_session, UserRole.ANALYST, username="lucas")
    incident = create_incident(
        db_session, create_user(db_session, UserRole.DRIVER), status=IncidentStatus.INVESTIGATING, assignee_id=lucas.id
    )

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Apenas incidentes abertos e sem responsável podem ser assumidos."}


def test_driver_cannot_assume_incident(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    driver = login_as(UserRole.DRIVER, "jose")
    incident = create_incident(db_session, driver)

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == FORBIDDEN


def test_assume_missing_incident_returns_404(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")

    response = db_client.post("/api/incidents/999999/assume", json={"version": 1})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Incidente não encontrado."}


def test_assume_without_version_returns_422(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")
    incident = create_incident(db_session, create_user(db_session, UserRole.DRIVER))

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Dados inválidos. Revise os campos e tente novamente."}


def test_assume_requires_login(db_client: TestClient) -> None:
    response = db_client.post("/api/incidents/1/assume", json={"version": 1})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

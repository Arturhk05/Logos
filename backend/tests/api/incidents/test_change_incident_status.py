from datetime import UTC, datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.incidents.enums import IncidentStatus
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.api.conftest import LoginAs
from tests.factories import create_incident, create_user

CONFLICT_MESSAGE = "Este incidente foi alterado por outra pessoa. Confira o estado atual."
FORBIDDEN = {"detail": "Você não tem permissão para realizar esta ação."}
INVALID_REQUEST = {"detail": "Dados inválidos. Revise os campos e tente novamente."}


def _investigating_incident(db_session: Session, assignee: User, **overrides: object) -> int:
    driver = create_user(db_session, UserRole.DRIVER)
    return create_incident(db_session, driver, status=IncidentStatus.INVESTIGATING, assignee_id=assignee.id, **overrides).id


def test_assignee_closes_incident_with_reason(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "CLOSED", "version": 1, "reason": "Pneu trocado"})

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "CLOSED"
    assert body["closed_by"] == {"id": camila.id, "username": "camila"}
    assert body["closure_reason"] == "Pneu trocado"
    assert body["closed_at"] is not None
    assert body["version"] == 2


def test_supervisor_returns_incident_of_another_analyst_to_the_queue(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.SUPERVISOR, "roberto")
    camila = create_user(db_session, UserRole.ANALYST, username="camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "OPEN"
    assert response.json()["assignee"] is None


def test_analyst_who_is_not_the_assignee_gets_403(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "lucas")
    camila = create_user(db_session, UserRole.ANALYST, username="camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Apenas o responsável pelo incidente ou um supervisor pode alterar seu status."}


def test_driver_cannot_change_status(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    driver = login_as(UserRole.DRIVER, "jose")
    incident = create_incident(db_session, driver)

    response = db_client.patch(f"/api/incidents/{incident.id}/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == FORBIDDEN


def test_closing_without_reason_returns_422(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "CLOSED", "version": 1})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Informe o motivo do encerramento."}


def test_closed_incident_cannot_change_status(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    roberto = login_as(UserRole.SUPERVISOR, "roberto")
    incident = create_incident(
        db_session,
        create_user(db_session, UserRole.DRIVER),
        status=IncidentStatus.CLOSED,
        assignee_id=roberto.id,
        closed_by_id=roberto.id,
        closed_at=datetime(2026, 10, 18, 11, tzinfo=UTC),
        closure_reason="Pista liberada",
    )

    response = db_client.patch(f"/api/incidents/{incident.id}/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Não é possível alterar um incidente de Fechado para Aberto."}


def test_change_status_with_outdated_version_returns_409_with_current_state(
    db_client: TestClient, db_session: Session, login_as: LoginAs
) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila, version=2)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == CONFLICT_MESSAGE
    assert response.json()["current"]["status"] == "INVESTIGATING"
    assert response.json()["current"]["version"] == 2


def test_unknown_status_returns_422(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "RESOLVED", "version": 1})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST


def test_reason_longer_than_500_characters_returns_422(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "CLOSED", "version": 1, "reason": "a" * 501})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST


def test_change_status_of_missing_incident_returns_404(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.SUPERVISOR, "roberto")

    response = db_client.patch("/api/incidents/999999/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Incidente não encontrado."}


def test_change_status_requires_login(db_client: TestClient) -> None:
    response = db_client.patch("/api/incidents/1/status", json={"status": "OPEN", "version": 1})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_reason_with_exactly_500_characters_is_accepted(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "CLOSED", "version": 1, "reason": "a" * 500})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["closure_reason"] == "a" * 500


def test_reason_length_is_checked_without_surrounding_whitespace(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(
        f"/api/incidents/{incident_id}/status", json={"status": "CLOSED", "version": 1, "reason": "a" * 495 + " \n" * 5}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["closure_reason"] == "a" * 495


def test_reason_with_null_character_returns_422(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident_id = _investigating_incident(db_session, camila)

    response = db_client.patch(f"/api/incidents/{incident_id}/status", json={"status": "CLOSED", "version": 1, "reason": "Pneu\x00trocado"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST

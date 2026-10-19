from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.users.enums import UserRole
from tests.api.conftest import LoginAs
from tests.factories import create_incident, create_user

NOT_FOUND = {"detail": "Incidente não encontrado."}


def test_detail_of_closed_incident_shows_who_closed_it_and_why(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    analyst = login_as(UserRole.ANALYST, "camila")
    driver = create_user(db_session, UserRole.DRIVER, username="jose")
    incident = create_incident(
        db_session,
        driver,
        category=IncidentCategory.ROAD_BLOCKAGE,
        criticality=Criticality.MEDIUM,
        status=IncidentStatus.CLOSED,
        location="BR-101, km 12",
        description="Queda de barreira bloqueando as duas faixas",
        assignee_id=analyst.id,
        closed_by_id=analyst.id,
        closed_at=datetime(2026, 10, 18, 11, 30, tzinfo=UTC),
        closure_reason="Pista liberada pela concessionária",
        version=3,
        created_at=datetime(2026, 10, 18, 9, tzinfo=UTC),
        updated_at=datetime(2026, 10, 18, 11, 30, tzinfo=UTC),
    )

    response = db_client.get(f"/api/incidents/{incident.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": incident.id,
        "category": "ROAD_BLOCKAGE",
        "criticality": "MEDIUM",
        "status": "CLOSED",
        "location": "BR-101, km 12",
        "description": "Queda de barreira bloqueando as duas faixas",
        "reporter": {"id": driver.id, "username": "jose"},
        "assignee": {"id": analyst.id, "username": "camila"},
        "closed_by": {"id": analyst.id, "username": "camila"},
        "closed_at": "2026-10-18T11:30:00Z",
        "closure_reason": "Pista liberada pela concessionária",
        "version": 3,
        "created_at": "2026-10-18T09:00:00Z",
        "updated_at": "2026-10-18T11:30:00Z",
        "events": [],
    }


def test_driver_sees_detail_of_own_incident(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    driver = login_as(UserRole.DRIVER, "jose")
    incident = create_incident(db_session, driver)

    response = db_client.get(f"/api/incidents/{incident.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["reporter"] == {"id": driver.id, "username": "jose"}
    assert response.json()["assignee"] is None


def test_driver_gets_404_for_incident_of_another_driver(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")
    other_driver = create_user(db_session, UserRole.DRIVER)
    incident = create_incident(db_session, other_driver)

    response = db_client.get(f"/api/incidents/{incident.id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == NOT_FOUND


def test_detail_of_missing_incident_returns_404(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.SUPERVISOR, "roberto")

    response = db_client.get("/api/incidents/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == NOT_FOUND


def test_detail_requires_login(db_client: TestClient) -> None:
    response = db_client.get("/api/incidents/1")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.SUPERVISOR])
def test_central_user_sees_incident_assigned_to_someone_else(
    db_client: TestClient, db_session: Session, login_as: LoginAs, role: UserRole
) -> None:
    login_as(role, "central")
    driver = create_user(db_session, UserRole.DRIVER)
    other_analyst = create_user(db_session, UserRole.ANALYST, username="lucas")
    incident = create_incident(db_session, driver, status=IncidentStatus.INVESTIGATING, assignee_id=other_analyst.id)

    response = db_client.get(f"/api/incidents/{incident.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["assignee"] == {"id": other_analyst.id, "username": "lucas"}


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "", None),
        ("POST", "/assume", {"version": 1}),
        ("PATCH", "/status", {"status": "OPEN", "version": 1}),
    ],
)
@pytest.mark.parametrize("incident_id", ["0", "2147483648", "99999999999999999999"])
def test_incident_id_out_of_range_returns_422(
    db_client: TestClient, login_as: LoginAs, method: str, path: str, body: dict[str, object] | None, incident_id: str
) -> None:
    login_as(UserRole.SUPERVISOR, "roberto")

    response = db_client.request(method, f"/api/incidents/{incident_id}{path}", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Dados inválidos. Revise os campos e tente novamente."}


# --- change log (RN-12, US-12) -----------------------------------------------

REPORT = {"category": "MECHANICAL_PROBLEM", "location": "BR-116, km 230", "description": "Pneu furado no acostamento"}


def _changes(body: dict[str, Any]) -> list[tuple[str, str | None, str, str | None]]:
    """The events of an incident in the response, without their timestamps."""
    for event in body["events"]:
        assert event["created_at"] is not None
    return [(event["actor"]["username"], event["from_status"], event["to_status"], event["reason"]) for event in body["events"]]


def test_detail_lists_the_events_oldest_first(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")
    incident = db_client.post("/api/incidents", json=REPORT, headers={"Idempotency-Key": str(uuid4())}).json()
    login_as(UserRole.ANALYST, "camila")
    db_client.post(f"/api/incidents/{incident['id']}/assume", json={"version": 1})
    login_as(UserRole.SUPERVISOR, "roberto")
    db_client.patch(f"/api/incidents/{incident['id']}/status", json={"version": 2, "status": "OPEN", "reason": "Analista saiu do turno"})
    login_as(UserRole.ANALYST, "lucas")
    db_client.post(f"/api/incidents/{incident['id']}/assume", json={"version": 3})

    response = db_client.get(f"/api/incidents/{incident['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert _changes(response.json()) == [
        ("jose", None, "OPEN", None),
        ("camila", "OPEN", "INVESTIGATING", None),
        ("roberto", "INVESTIGATING", "OPEN", "Analista saiu do turno"),
        ("lucas", "OPEN", "INVESTIGATING", None),
    ]


def test_assume_response_includes_the_new_event(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")
    incident = create_incident(db_session, create_user(db_session, UserRole.DRIVER))

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_200_OK
    assert _changes(response.json()) == [("camila", "OPEN", "INVESTIGATING", None)]


def test_status_change_response_includes_the_new_event(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    incident = create_incident(
        db_session, create_user(db_session, UserRole.DRIVER), status=IncidentStatus.INVESTIGATING, assignee_id=camila.id
    )

    response = db_client.patch(f"/api/incidents/{incident.id}/status", json={"version": 1, "status": "CLOSED", "reason": "Pneu trocado"})

    assert response.status_code == status.HTTP_200_OK
    assert _changes(response.json()) == [("camila", "INVESTIGATING", "CLOSED", "Pneu trocado")]


def test_conflict_response_includes_the_current_events(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    incident = create_incident(db_session, create_user(db_session, UserRole.DRIVER))
    login_as(UserRole.ANALYST, "camila")
    db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})
    login_as(UserRole.ANALYST, "lucas")

    response = db_client.post(f"/api/incidents/{incident.id}/assume", json={"version": 1})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert _changes(response.json()["current"]) == [("camila", "OPEN", "INVESTIGATING", None)]


def test_retried_report_keeps_a_single_event(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")
    key = {"Idempotency-Key": str(uuid4())}
    db_client.post("/api/incidents", json=REPORT, headers=key)

    retried = db_client.post("/api/incidents", json=REPORT, headers=key)

    assert _changes(retried.json()) == [("jose", None, "OPEN", None)]
    assert _changes(db_client.get(f"/api/incidents/{retried.json()['id']}").json()) == [("jose", None, "OPEN", None)]

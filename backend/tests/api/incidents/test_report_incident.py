from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.modules.users.enums import UserRole
from tests.api.conftest import LoginAs

FORBIDDEN = {"detail": "Você não tem permissão para realizar esta ação."}
INVALID_REQUEST = {"detail": "Dados inválidos. Revise os campos e tente novamente."}
REPORT = {"category": "MECHANICAL_PROBLEM", "location": "BR-116, km 230", "description": "Pneu furado no acostamento"}


def _key() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid4())}


def test_driver_reports_incident_with_suggested_criticality(db_client: TestClient, login_as: LoginAs) -> None:
    jose = login_as(UserRole.DRIVER, "jose")

    response = db_client.post("/api/incidents", json=REPORT | {"category": "ACCIDENT_WITH_VICTIMS"}, headers=_key())

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["category"] == "ACCIDENT_WITH_VICTIMS"
    assert body["criticality"] == "HIGH"
    assert body["status"] == "OPEN"
    assert body["location"] == "BR-116, km 230"
    assert body["assignee"] is None
    assert body["reporter"] == {"id": jose.id, "username": "jose"}
    assert body["version"] == 1


def test_repeated_report_with_same_key_returns_the_same_incident(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")
    key = _key()

    first = db_client.post("/api/incidents", json=REPORT, headers=key)
    second = db_client.post("/api/incidents", json=REPORT, headers=key)

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_201_CREATED
    assert second.json()["id"] == first.json()["id"]


def test_accident_with_victims_below_high_returns_422(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.post("/api/incidents", json=REPORT | {"category": "ACCIDENT_WITH_VICTIMS", "criticality": "LOW"}, headers=_key())

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Acidentes com vítimas são sempre de criticidade alta."}


@pytest.mark.parametrize("role", [UserRole.ANALYST, UserRole.SUPERVISOR])
def test_central_user_cannot_report_incident(db_client: TestClient, login_as: LoginAs, role: UserRole) -> None:
    login_as(role, "central")

    response = db_client.post("/api/incidents", json=REPORT, headers=_key())

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == FORBIDDEN


def test_report_without_idempotency_key_returns_422(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.post("/api/incidents", json=REPORT)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST


def test_report_with_blank_location_returns_422(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.post("/api/incidents", json=REPORT | {"location": "   "}, headers=_key())

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST


def test_report_requires_login(db_client: TestClient) -> None:
    response = db_client.post("/api/incidents", json=REPORT, headers=_key())

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_report_with_invalid_idempotency_key_returns_422(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.post("/api/incidents", json=REPORT, headers={"Idempotency-Key": "abc"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST


def test_repeated_report_with_different_data_keeps_the_first_incident(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")
    key = _key()
    first = db_client.post("/api/incidents", json=REPORT, headers=key)

    second = db_client.post("/api/incidents", json=REPORT | {"description": "Outra descrição"}, headers=key)

    assert second.status_code == status.HTTP_201_CREATED
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["description"] == "Pneu furado no acostamento"


def test_idempotency_key_header_is_published_with_its_canonical_name(client: TestClient) -> None:
    operation = client.get("/api/openapi.json").json()["paths"]["/api/incidents"]["post"]

    headers = [parameter["name"] for parameter in operation["parameters"] if parameter["in"] == "header"]

    assert headers == ["Idempotency-Key"]


@pytest.mark.parametrize("field", ["location", "description"])
def test_report_with_null_character_returns_422(db_client: TestClient, login_as: LoginAs, field: str) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.post("/api/incidents", json=REPORT | {field: "Pneu\x00furado"}, headers=_key())

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST

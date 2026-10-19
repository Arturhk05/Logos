from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.api.conftest import LoginAs
from tests.factories import create_incident, create_user

INVALID_REQUEST = {"detail": "Dados inválidos. Revise os campos e tente novamente."}


def _at(hour: int) -> datetime:
    return datetime(2026, 10, 18, hour, tzinfo=UTC)


def _closed(db_session: Session, reporter: User, closer: User, closed_at_hour: int, **overrides: Any) -> int:
    fields: dict[str, Any] = {
        "status": IncidentStatus.CLOSED,
        "assignee_id": closer.id,
        "closed_by_id": closer.id,
        "closed_at": _at(closed_at_hour),
        "closure_reason": "Resolvido",
        "created_at": _at(1),
    }
    return create_incident(db_session, reporter, **(fields | overrides)).id


def test_history_lists_closed_incidents_with_who_closed_them(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    driver = create_user(db_session, UserRole.DRIVER)
    older_id = _closed(db_session, driver, camila, 10)
    newer_id = _closed(
        db_session,
        driver,
        camila,
        11,
        status=IncidentStatus.INCONCLUSIVE,
        category=IncidentCategory.ADVERSE_WEATHER,
        criticality=Criticality.LOW,
        location="BR-116, km 10",
        created_at=_at(9),
    )
    create_incident(db_session, driver, created_at=_at(12))

    response = db_client.get("/api/incidents/history")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert [item["id"] for item in body["items"]] == [newer_id, older_id]
    assert body["items"][0] == {
        "id": newer_id,
        "category": "ADVERSE_WEATHER",
        "criticality": "LOW",
        "status": "INCONCLUSIVE",
        "location": "BR-116, km 10",
        "created_at": "2026-10-18T09:00:00Z",
        "assignee": {"id": camila.id, "username": "camila"},
        "closed_by": {"id": camila.id, "username": "camila"},
        "closed_at": "2026-10-18T11:00:00Z",
    }
    assert (body["total"], body["page"], body["page_size"]) == (2, 1, 20)


def test_history_applies_filters_and_pagination_from_the_query_string(
    db_client: TestClient, db_session: Session, login_as: LoginAs
) -> None:
    roberto = login_as(UserRole.SUPERVISOR, "roberto")
    driver = create_user(db_session, UserRole.DRIVER)
    high = {"criticality": Criticality.HIGH, "category": IncidentCategory.ROAD_BLOCKAGE}
    oldest_id = _closed(db_session, driver, roberto, 8, **high)
    _closed(db_session, driver, roberto, 9, **high)
    _closed(db_session, driver, roberto, 10, **high)
    _closed(db_session, driver, roberto, 11, **(high | {"criticality": Criticality.LOW}))
    _closed(db_session, driver, roberto, 12, **(high | {"status": IncidentStatus.INCONCLUSIVE}))
    _closed(db_session, driver, roberto, 13, **(high | {"category": IncidentCategory.ADVERSE_WEATHER}))

    response = db_client.get("/api/incidents/history?status=CLOSED&criticality=HIGH&category=ROAD_BLOCKAGE&page=2&page_size=2")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert [item["id"] for item in body["items"]] == [oldest_id]
    assert (body["total"], body["page"], body["page_size"]) == (3, 2, 2)


def test_history_with_active_status_returns_422(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.ANALYST, "camila")

    response = db_client.get("/api/incidents/history?status=OPEN")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "O histórico mostra apenas incidentes encerrados."}


@pytest.mark.parametrize("query", ["page=0", "page=100001", "page=100000000000000000", "page_size=0", "page_size=101"])
def test_history_with_invalid_page_returns_422(db_client: TestClient, login_as: LoginAs, query: str) -> None:
    login_as(UserRole.ANALYST, "camila")

    response = db_client.get(f"/api/incidents/history?{query}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == INVALID_REQUEST


def test_driver_cannot_see_history(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.get("/api/incidents/history")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Você não tem permissão para realizar esta ação."}


def test_history_requires_login(db_client: TestClient) -> None:
    response = db_client.get("/api/incidents/history")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_history_does_not_show_phones(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    camila = login_as(UserRole.ANALYST, "camila")
    _closed(db_session, create_user(db_session, UserRole.DRIVER, phone="5500900000001"), camila, 10)

    response = db_client.get("/api/incidents/history")

    assert response.json()["items"]
    assert "phone" not in response.text
    assert "5500900000001" not in response.text

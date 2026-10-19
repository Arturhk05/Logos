from collections.abc import Iterator
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.enums import UserRole
from app.shared.db.session import get_session
from tests.api.conftest import LoginAs
from tests.conftest import BASE_URL


def test_failed_commit_is_reported_as_an_error_not_as_success(db_client: TestClient, db_session: Session, login_as: LoginAs) -> None:
    """The commit must happen before the response is sent, otherwise the driver sees a report that was never saved."""
    login_as(UserRole.DRIVER, "jose")

    def session_whose_commit_fails() -> Iterator[Session]:
        with db_session.begin_nested():
            yield db_session
        raise RuntimeError("commit failed")

    db_client.app.dependency_overrides[get_session] = session_whose_commit_fails  # type: ignore[attr-defined]
    with TestClient(db_client.app, base_url=BASE_URL, cookies=db_client.cookies, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/incidents",
            json={"category": "MECHANICAL_PROBLEM", "location": "BR-116, km 230", "description": "Pneu furado"},
            headers={"Idempotency-Key": str(uuid4())},
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

from typing import Annotated, cast

import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import require_role
from app.modules.auth.security import hash_password
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.factories import create_user

PASSWORD = "senha-correta"
PASSWORD_HASH = hash_password(PASSWORD)
SUPERVISOR_ROUTE = "/api/test-supervisor-only"
CENTRAL_ROUTE = "/api/test-central-only"


@pytest.fixture
def role_client(db_client: TestClient, db_session: Session) -> TestClient:
    create_user(db_session, UserRole.SUPERVISOR, username="supervisor", password_hash=PASSWORD_HASH)
    create_user(db_session, UserRole.ANALYST, username="analista", password_hash=PASSWORD_HASH)
    create_user(db_session, UserRole.DRIVER, username="motorista", password_hash=PASSWORD_HASH)

    def supervisor_only(actor: Annotated[User, Depends(require_role(UserRole.SUPERVISOR))]) -> dict[str, str]:
        return {"username": actor.username}

    def central_only(actor: Annotated[User, Depends(require_role(UserRole.ANALYST, UserRole.SUPERVISOR))]) -> dict[str, str]:
        return {"username": actor.username}

    app = cast(FastAPI, db_client.app)
    app.add_api_route(SUPERVISOR_ROUTE, supervisor_only)
    app.add_api_route(CENTRAL_ROUTE, central_only)
    return db_client


def _login(client: TestClient, username: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert response.status_code == status.HTTP_200_OK


def test_allowed_role_reaches_the_route(role_client: TestClient) -> None:
    _login(role_client, "supervisor")

    response = role_client.get(SUPERVISOR_ROUTE)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"username": "supervisor"}


def test_any_of_several_allowed_roles_reaches_the_route(role_client: TestClient) -> None:
    _login(role_client, "analista")

    response = role_client.get(CENTRAL_ROUTE)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"username": "analista"}


def test_other_role_gets_403(role_client: TestClient) -> None:
    _login(role_client, "motorista")

    response = role_client.get(SUPERVISOR_ROUTE)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Você não tem permissão para realizar esta ação."}


def test_anonymous_gets_401_before_role_check(role_client: TestClient) -> None:
    response = role_client.get(SUPERVISOR_ROUTE)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Sua sessão expirou. Entre novamente."}

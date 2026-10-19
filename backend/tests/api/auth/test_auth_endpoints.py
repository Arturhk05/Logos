import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth.security import hash_password
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.factories import create_user

PASSWORD = "senha-correta"
PASSWORD_HASH = hash_password(PASSWORD)
SESSION_EXPIRED = {"detail": "Sua sessão expirou. Entre novamente."}


@pytest.fixture
def supervisor(db_session: Session) -> User:
    return create_user(db_session, UserRole.SUPERVISOR, username="supervisor", password_hash=PASSWORD_HASH)


def _login(client: TestClient) -> TestClient:
    client.post("/api/auth/login", json={"username": "supervisor", "password": PASSWORD})
    return client


def test_login_returns_the_user_and_sets_the_session_cookie(db_client: TestClient, supervisor: User) -> None:
    response = db_client.post("/api/auth/login", json={"username": "supervisor", "password": PASSWORD})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": supervisor.id, "username": "supervisor", "role": "SUPERVISOR"}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("access_token=")
    for attribute in ("HttpOnly", "Secure", "SameSite=strict", "Path=/api", "Max-Age=28800"):
        assert attribute.lower() in cookie.lower()


def test_login_with_wrong_password_returns_401_without_cookie(db_client: TestClient, supervisor: User) -> None:
    response = db_client.post("/api/auth/login", json={"username": "supervisor", "password": "senha-errada"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Usuário ou senha inválidos."}
    assert "set-cookie" not in response.headers


def test_login_with_password_longer_than_72_bytes_returns_401(db_client: TestClient, supervisor: User) -> None:
    response = db_client.post("/api/auth/login", json={"username": "supervisor", "password": "a" * 100})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_returns_the_logged_in_user(db_client: TestClient, supervisor: User) -> None:
    response = _login(db_client).get("/api/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": supervisor.id, "username": "supervisor", "role": "SUPERVISOR"}


def test_me_does_not_show_the_driver_phone(db_client: TestClient, db_session: Session) -> None:
    create_user(db_session, UserRole.DRIVER, username="jose", password_hash=PASSWORD_HASH, phone="5500900000001")
    db_client.post("/api/auth/login", json={"username": "jose", "password": PASSWORD})

    response = db_client.get("/api/me")

    assert response.status_code == status.HTTP_200_OK
    assert "phone" not in response.json()


def test_me_without_session_returns_401(db_client: TestClient) -> None:
    response = db_client.get("/api/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == SESSION_EXPIRED


def test_logout_removes_the_session_cookie(db_client: TestClient, supervisor: User) -> None:
    response = _login(db_client).post("/api/auth/logout")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    cookie = response.headers["set-cookie"].lower()
    assert "access_token=" in cookie
    assert "max-age=0" in cookie
    assert "path=/api" in cookie
    assert db_client.get("/api/me").json() == SESSION_EXPIRED

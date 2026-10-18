from collections.abc import Callable
from functools import cache

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth.security import hash_password
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from tests.factories import create_user

TEST_PASSWORD = "senha-de-teste"

LoginAs = Callable[[UserRole, str], User]


@cache
def _test_password_hash() -> str:
    # bcrypt is slow on purpose, so the hash is computed once per test run.
    return hash_password(TEST_PASSWORD)


@pytest.fixture
def login_as(db_client: TestClient, db_session: Session) -> LoginAs:
    """Create a user with the given role and username and log `db_client` in as them."""

    def login(role: UserRole, username: str) -> User:
        user = create_user(db_session, role, username=username, password_hash=_test_password_hash())
        response = db_client.post("/api/auth/login", json={"username": username, "password": TEST_PASSWORD})
        assert response.status_code == 200
        return user

    return login

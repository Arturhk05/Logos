from datetime import timedelta

import pytest

from app.modules.auth.security import hash_password
from app.modules.auth.service import AuthService
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import AuthenticationError
from tests.factories import build_user
from tests.fakes import InMemoryUserRepository

PASSWORD = "senha-correta"
PASSWORD_HASH = hash_password(PASSWORD)
SECRET = "s" * 32
LIFETIME = timedelta(hours=8)
INVALID_CREDENTIALS = "Usuário ou senha inválidos."
SESSION_EXPIRED = "Sua sessão expirou. Entre novamente."


@pytest.fixture
def user() -> User:
    return build_user(UserRole.ANALYST, username="analista", password_hash=PASSWORD_HASH)


@pytest.fixture
def service(user: User) -> AuthService:
    return AuthService(InMemoryUserRepository(user), SECRET, LIFETIME)


def test_authenticate_returns_the_user_with_valid_credentials(service: AuthService, user: User) -> None:
    assert service.authenticate("analista", PASSWORD) is user


def test_authenticate_ignores_case_and_surrounding_spaces_in_username(service: AuthService, user: User) -> None:
    assert service.authenticate("  Analista ", PASSWORD) is user


def test_authenticate_rejects_wrong_password(service: AuthService) -> None:
    with pytest.raises(AuthenticationError) as error:
        service.authenticate("analista", "senha-errada")

    assert error.value.message == INVALID_CREDENTIALS


def test_authenticate_rejects_unknown_username(service: AuthService) -> None:
    with pytest.raises(AuthenticationError) as error:
        service.authenticate("ninguem", PASSWORD)

    assert error.value.message == INVALID_CREDENTIALS


def test_user_from_token_returns_the_token_owner(service: AuthService, user: User) -> None:
    assert service.user_from_token(service.issue_token(user)) is user


@pytest.mark.parametrize("token", [None, "lixo"], ids=["missing", "invalid"])
def test_user_from_token_rejects_missing_or_invalid_token(service: AuthService, token: str | None) -> None:
    with pytest.raises(AuthenticationError) as error:
        service.user_from_token(token)

    assert error.value.message == SESSION_EXPIRED


def test_user_from_token_rejects_token_of_removed_user(service: AuthService, user: User) -> None:
    token = service.issue_token(user)
    service_without_user = AuthService(InMemoryUserRepository(), SECRET, LIFETIME)

    with pytest.raises(AuthenticationError) as error:
        service_without_user.user_from_token(token)

    assert error.value.message == SESSION_EXPIRED


def test_authenticate_checks_a_password_even_for_unknown_username(service: AuthService, monkeypatch: pytest.MonkeyPatch) -> None:
    checked: list[str] = []

    def record_check(password: str, _password_hash: str) -> bool:
        checked.append(password)
        return False

    monkeypatch.setattr("app.modules.auth.service.verify_password", record_check)

    with pytest.raises(AuthenticationError):
        service.authenticate("ninguem", PASSWORD)

    assert checked == [PASSWORD]

import pytest
from pydantic import SecretStr, ValidationError

from app.shared.config import Settings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings also read the process environment, which `_env_file=None` does not ignore."""
    for name in ("ENVIRONMENT", "JWT_SECRET", "ACCESS_TOKEN_LIFETIME_MINUTES"):
        monkeypatch.delenv(name, raising=False)


def test_production_requires_a_strong_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", jwt_secret=SecretStr("curto"))

    settings = Settings(_env_file=None, environment="production", jwt_secret=SecretStr("x" * 32))

    assert settings.jwt_secret.get_secret_value() == "x" * 32


def test_rejected_secret_is_not_shown_in_the_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "almost-a-real-secret")

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    assert "almost-a-real-secret" not in str(error.value)


def test_development_works_without_jwt_secret() -> None:
    settings = Settings(_env_file=None, environment="development")

    assert settings.access_token_lifetime_minutes == 480


def test_token_lifetime_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, access_token_lifetime_minutes=0)

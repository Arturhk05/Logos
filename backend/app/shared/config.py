from functools import lru_cache
from typing import Literal, Self

from pydantic import PositiveInt, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-secret-do-not-use-in-production"  # noqa: S105 (rejected in production)
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    # Without hide_input_in_errors, a rejected JWT_SECRET would be printed in the startup error.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", hide_input_in_errors=True)

    environment: Literal["development", "test", "production"] = "development"
    database_url: PostgresDsn = PostgresDsn("postgresql+psycopg://logos:logos@localhost:5432/logos")
    jwt_secret: SecretStr = SecretStr(DEVELOPMENT_JWT_SECRET)
    access_token_lifetime_minutes: PositiveInt = 480

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> Self:
        # Anyone who knows the secret can forge a token for any user.
        secret = self.jwt_secret.get_secret_value()
        if self.environment == "production" and (secret == DEVELOPMENT_JWT_SECRET or len(secret) < MIN_JWT_SECRET_LENGTH):
            raise ValueError(f"JWT_SECRET must be set to at least {MIN_JWT_SECRET_LENGTH} characters in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

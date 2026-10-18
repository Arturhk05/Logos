from datetime import UTC, datetime, timedelta

import jwt

from app.modules.auth.security import create_access_token, hash_password, read_access_token, verify_password
from tests.factories import build_user

PASSWORD = "senha-correta"
PASSWORD_HASH = hash_password(PASSWORD)
SECRET = "s" * 32
LIFETIME = timedelta(hours=8)


def test_verify_password_accepts_the_hashed_password() -> None:
    assert verify_password(PASSWORD, PASSWORD_HASH) is True


def test_verify_password_rejects_a_wrong_password() -> None:
    assert verify_password("senha-errada", PASSWORD_HASH) is False


def test_verify_password_rejects_passwords_longer_than_bcrypt_limit() -> None:
    assert verify_password("a" * 100, PASSWORD_HASH) is False


def test_hash_password_does_not_store_the_password() -> None:
    assert PASSWORD not in PASSWORD_HASH
    assert PASSWORD_HASH.startswith("$2b$")


def test_access_token_carries_only_the_user_id() -> None:
    user = build_user()

    token = create_access_token(user, SECRET, LIFETIME)

    assert read_access_token(token, SECRET) == user.id
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert set(claims) == {"sub", "iat", "exp"}
    assert claims["sub"] == str(user.id)
    assert claims["exp"] - claims["iat"] == 28800


def test_read_access_token_rejects_expired_token() -> None:
    token = create_access_token(build_user(), SECRET, timedelta(seconds=-1))

    assert read_access_token(token, SECRET) is None


def test_read_access_token_rejects_token_signed_with_another_secret() -> None:
    token = create_access_token(build_user(), "o" * 32, LIFETIME)

    assert read_access_token(token, SECRET) is None


def test_read_access_token_rejects_unsigned_token() -> None:
    token = jwt.encode({"sub": "1"}, key=None, algorithm="none")

    assert read_access_token(token, SECRET) is None


def test_read_access_token_rejects_non_numeric_subject() -> None:
    expires_at = datetime.now(UTC) + LIFETIME
    token = jwt.encode({"sub": "abc", "exp": expires_at}, SECRET, algorithm="HS256")

    assert read_access_token(token, SECRET) is None


def test_read_access_token_rejects_garbage() -> None:
    assert read_access_token("nao-e-um-token", SECRET) is None

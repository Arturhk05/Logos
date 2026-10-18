from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.modules.users.models import User

ALGORITHM = "HS256"
BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    encoded = password.encode()
    if len(encoded) > BCRYPT_MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(encoded, password_hash.encode())


def create_access_token(user: User, secret: str, lifetime: timedelta) -> str:
    issued_at = datetime.now(UTC)
    claims = {"sub": str(user.id), "iat": issued_at, "exp": issued_at + lifetime}
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def read_access_token(token: str, secret: str) -> int | None:
    """Return the id of the user the token was issued to, or None if it is invalid or expired."""
    try:
        claims = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
        return int(claims["sub"])
    except jwt.InvalidTokenError, ValueError:
        return None

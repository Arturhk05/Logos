from datetime import timedelta

from app.modules.auth.security import create_access_token, read_access_token, verify_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.shared.errors import AuthenticationError

INVALID_CREDENTIALS_MESSAGE = "Usuário ou senha inválidos."
SESSION_EXPIRED_MESSAGE = "Sua sessão expirou. Entre novamente."

# bcrypt hash (cost 12) of a random, unknown password.
UNKNOWN_USER_PASSWORD_HASH = "$2b$12$WG7CsDgYJqc5AZhGx1FaO.rGj58QFDUCpZsQ2Qjz0zf8rz8HpIeK2"  # noqa: S105


class AuthService:
    def __init__(self, users: UserRepository, secret: str, token_lifetime: timedelta) -> None:
        self._users = users
        self._secret = secret
        self._token_lifetime = token_lifetime

    def authenticate(self, username: str, password: str) -> User:
        """Return the user owning these credentials, without revealing which of the two is wrong."""
        user = self._users.get_by_username(username.strip().lower())
        # Checking a password even for unknown users keeps the response time from revealing which usernames exist.
        password_hash = user.password_hash if user else UNKNOWN_USER_PASSWORD_HASH
        if not verify_password(password, password_hash) or user is None:
            raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE)
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(user, self._secret, self._token_lifetime)

    def user_from_token(self, token: str | None) -> User:
        user_id = read_access_token(token, self._secret) if token else None
        user = self._users.get(user_id) if user_id is not None else None
        if user is None:
            raise AuthenticationError(SESSION_EXPIRED_MESSAGE)
        return user

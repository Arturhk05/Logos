from typing import Any


class DomainError(Exception):
    """Base class for errors raised by business rules.

    The message is meant to be shown to the end user, so it is written in Portuguese
    and without technical terms.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """The requested resource does not exist."""


class PermissionDeniedError(DomainError):
    """The user's role does not allow the action."""


class BusinessRuleError(DomainError):
    """The action is not allowed in the current state of the resource."""


class ConflictError(DomainError):
    """The resource was changed by someone else since the user last saw it."""

    def __init__(self, message: str, current: Any = None) -> None:
        super().__init__(message)
        self.current = current

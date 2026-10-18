from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.shared.errors import BusinessRuleError, ConflictError, DomainError, NotFoundError, PermissionDeniedError

ERROR_STATUS: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    BusinessRuleError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ConflictError: status.HTTP_409_CONFLICT,
}


def register_error_handlers(app: FastAPI) -> None:
    for error_class, status_code in ERROR_STATUS.items():
        app.add_exception_handler(error_class, _respond_with(status_code))


def _respond_with(status_code: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(_: Request, error: Exception) -> JSONResponse:
        if not isinstance(error, DomainError):
            raise error
        return JSONResponse(status_code=status_code, content={"detail": error.message})

    return handler

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException

from app.shared.errors import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

ERROR_STATUS: dict[type[DomainError], int] = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    BusinessRuleError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ConflictError: status.HTTP_409_CONFLICT,
}

NOT_FOUND_MESSAGE = "Não encontramos o que você procurava."
INVALID_REQUEST_MESSAGE = "Dados inválidos. Revise os campos e tente novamente."
UNEXPECTED_ERROR_MESSAGE = "Ocorreu um erro inesperado. Tente novamente em instantes."
UNAVAILABLE_MESSAGE = "O sistema está temporariamente indisponível. Tente novamente em instantes."


def register_error_handlers(app: FastAPI) -> None:
    for error_class, status_code in ERROR_STATUS.items():
        app.add_exception_handler(error_class, _respond_with(status_code))
    app.add_exception_handler(OperationalError, _database_unavailable)
    app.add_exception_handler(HTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _invalid_request)
    app.add_exception_handler(Exception, _unexpected_error)


def _respond_with(status_code: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(_: Request, error: Exception) -> JSONResponse:
        if not isinstance(error, DomainError):
            raise error
        return JSONResponse(status_code=status_code, content={"detail": error.message})

    return handler


async def _database_unavailable(request: Request, error: Exception) -> JSONResponse:
    # Connection failures and timeouts. The driver's message names the database host, so it goes only to the log.
    logger.error("Database unavailable on %s", request.url.path, exc_info=error)
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": UNAVAILABLE_MESSAGE})


async def _http_error(_: Request, error: Exception) -> JSONResponse:
    # Raised by the framework itself (unknown route, wrong method), with English text the user would see.
    if not isinstance(error, HTTPException):
        raise error
    message = NOT_FOUND_MESSAGE if error.status_code == status.HTTP_404_NOT_FOUND else UNEXPECTED_ERROR_MESSAGE
    return JSONResponse(status_code=error.status_code, content={"detail": message}, headers=error.headers)


async def _invalid_request(request: Request, error: Exception) -> JSONResponse:
    # Pydantic's error list is technical and in English; the frontend validates the forms before sending.
    # Only field and message are logged: the rejected input may contain a password.
    if isinstance(error, RequestValidationError):
        fields = [{"loc": detail["loc"], "msg": detail["msg"]} for detail in error.errors()]
        logger.warning("Invalid request on %s: %s", request.url.path, fields)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": INVALID_REQUEST_MESSAGE})


async def _unexpected_error(_: Request, __: Exception) -> JSONResponse:
    # Starlette re-raises the exception after this response, so the server still logs the traceback.
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": UNEXPECTED_ERROR_MESSAGE})

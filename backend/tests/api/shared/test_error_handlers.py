from collections.abc import Iterator

import psycopg
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import create_app
from app.shared.config import get_settings
from app.shared.db.session import get_engine, get_session_factory
from app.shared.errors import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
)

ERROR_PATH = "/api/test-error"


def _client_raising(error: Exception) -> TestClient:
    app = create_app()

    def raise_error() -> None:
        raise error

    app.add_api_route(ERROR_PATH, raise_error)
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (NotFoundError("Incidente não encontrado."), status.HTTP_404_NOT_FOUND),
        (PermissionDeniedError("Apenas o responsável pode alterar este incidente."), status.HTTP_403_FORBIDDEN),
        (BusinessRuleError("Informe o motivo do encerramento."), status.HTTP_422_UNPROCESSABLE_CONTENT),
        (ConflictError("Este incidente foi alterado por outra pessoa.", current=object()), status.HTTP_409_CONFLICT),
        (AuthenticationError("Usuário ou senha inválidos."), status.HTTP_401_UNAUTHORIZED),
    ],
    ids=["not_found", "permission_denied", "business_rule", "conflict", "authentication"],
)
def test_domain_error_is_returned_with_its_status_and_message(error: DomainError, expected_status: int) -> None:
    with _client_raising(error) as client:
        response = client.get(ERROR_PATH)

    assert response.status_code == expected_status
    assert response.json() == {"detail": error.message}


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Without debug mode, Starlette uses the 500 handler instead of rendering the traceback."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "p" * 32)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.usefixtures("production")
def test_unexpected_error_returns_generic_message_without_internal_details() -> None:
    with _client_raising(RuntimeError("could not connect to postgresql://logos:secret@db")) as client:
        response = client.get(ERROR_PATH)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Ocorreu um erro inesperado. Tente novamente em instantes."}


@pytest.mark.usefixtures("production")
def test_database_unavailable_returns_503_without_internal_details(caplog: pytest.LogCaptureFixture) -> None:
    driver_error = psycopg.OperationalError('connection to server at "logos-db.abc.rds.amazonaws.com", port 5432 failed')
    with _client_raising(OperationalError("SELECT 1", {}, driver_error)) as client:
        response = client.get(ERROR_PATH)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "O sistema está temporariamente indisponível. Tente novamente em instantes."}
    assert "rds.amazonaws.com" not in response.text
    assert "rds.amazonaws.com" in caplog.text


@pytest.fixture
def database_down(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Nothing listens on port 1, so every connection is refused.
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://logos:logos@127.0.0.1:1/logos")
    for cached in (get_settings, get_engine, get_session_factory):
        cached.cache_clear()
    yield
    for cached in (get_settings, get_engine, get_session_factory):
        cached.cache_clear()


@pytest.mark.usefixtures("database_down")
def test_request_with_database_down_returns_503() -> None:
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.post("/api/auth/login", json={"username": "camila", "password": "logos123"})

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "O sistema está temporariamente indisponível. Tente novamente em instantes."}


VALIDATION_PATH = "/api/test-validation"


def _client_validating_quantity() -> TestClient:
    app = create_app()

    def endpoint(quantity: int) -> None:
        pass

    app.add_api_route(VALIDATION_PATH, endpoint)
    return TestClient(app)


def test_invalid_request_returns_generic_message_without_validation_details() -> None:
    with _client_validating_quantity() as client:
        response = client.get(VALIDATION_PATH, params={"quantity": "abc"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "Dados inválidos. Revise os campos e tente novamente."}


def test_invalid_request_logs_the_invalid_fields_without_their_values(caplog: pytest.LogCaptureFixture) -> None:
    with _client_validating_quantity() as client:
        client.get(VALIDATION_PATH, params={"quantity": "s3cr3t-value"})

    assert "quantity" in caplog.text
    assert "s3cr3t-value" not in caplog.text


def test_unknown_route_returns_not_found_in_portuguese(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Não encontramos o que você procurava."}


def test_id_that_does_not_match_the_route_returns_not_found_in_portuguese(client: TestClient) -> None:
    response = client.get("/api/incidents/abc")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Não encontramos o que você procurava."}


def test_wrong_method_keeps_its_status_and_allow_header_with_a_generic_message(client: TestClient) -> None:
    response = client.delete("/api/health")

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.headers["allow"] == "GET"
    assert response.json() == {"detail": "Ocorreu um erro inesperado. Tente novamente em instantes."}

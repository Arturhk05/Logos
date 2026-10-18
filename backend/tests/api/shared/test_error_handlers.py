import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.errors import BusinessRuleError, ConflictError, DomainError, NotFoundError, PermissionDeniedError

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
    ],
    ids=["not_found", "permission_denied", "business_rule", "conflict"],
)
def test_domain_error_is_returned_with_its_status_and_message(error: DomainError, expected_status: int) -> None:
    with _client_raising(error) as client:
        response = client.get(ERROR_PATH)

    assert response.status_code == expected_status
    assert response.json() == {"detail": error.message}

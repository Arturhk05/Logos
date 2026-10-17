from fastapi import status
from fastapi.testclient import TestClient


def test_health_check_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

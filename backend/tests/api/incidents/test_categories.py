from fastapi import status
from fastapi.testclient import TestClient

from app.modules.users.enums import UserRole
from tests.api.conftest import LoginAs


def test_categories_list_labels_and_suggested_criticality(db_client: TestClient, login_as: LoginAs) -> None:
    login_as(UserRole.DRIVER, "jose")

    response = db_client.get("/api/categories")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"category": "VEHICLE_ACCIDENT", "label": "Acidente com Veículo", "suggested_criticality": "HIGH", "criticality_locked": False},
        {"category": "ACCIDENT_WITH_VICTIMS", "label": "Acidente com Vítimas", "suggested_criticality": "HIGH", "criticality_locked": True},
        {
            "category": "ADVERSE_WEATHER",
            "label": "Condição Climática Atípica na Pista",
            "suggested_criticality": "MEDIUM",
            "criticality_locked": False,
        },
        {"category": "MECHANICAL_PROBLEM", "label": "Problema Mecânico", "suggested_criticality": "MEDIUM", "criticality_locked": False},
        {"category": "ROAD_BLOCKAGE", "label": "Bloqueio de Pista", "suggested_criticality": "MEDIUM", "criticality_locked": False},
    ]


def test_categories_require_login(db_client: TestClient) -> None:
    response = db_client.get("/api/categories")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

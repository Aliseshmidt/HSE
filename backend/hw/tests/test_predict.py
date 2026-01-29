from http import HTTPStatus
from fastapi.testclient import TestClient
import pytest
from main import app
from model import ensure_model_exists


def test_predict_violation_true(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": False,
            "item_id": 10,
            "name": "test item",
            "description": "test description",
            "category": 50,
            "images_qty": 1
        },
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_violation_false(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 2,
            "is_verified_seller": True,
            "item_id": 11,
            "name": "test item 2",
            "description": "test description with more text",
            "category": 30,
            "images_qty": 5
        },
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_invalid_data_types(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 3,
            "is_verified_seller": False,
            "item_id": 12,
            "name": 123,
            "description": "test",
            "category": 3,
            "images_qty": 0,
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_predict_model_not_loaded(app_client: TestClient):
    original_model = app.state.model
    app.state.model = None
    
    try:
        response = app_client.post(
            "/predict",
            json={
                "seller_id": 4,
                "is_verified_seller": True,
                "item_id": 13,
                "name": "test",
                "description": "test",
                "category": 1,
                "images_qty": 1,
            },
        )

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert "модель" in response.json()["detail"].lower() or "model" in response.json()["detail"].lower()
    finally:
        app.state.model = original_model

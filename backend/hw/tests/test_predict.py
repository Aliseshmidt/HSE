from http import HTTPStatus
from fastapi.testclient import TestClient
import pytest


def test_predict_positive(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": True,
            "item_id": 10,
            "name": "test",
            "description": "test",
            "category": 1,
            "images_qty": 5,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["is_allowed"] is True

def test_predict_unverified(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 2,
            "is_verified_seller": False,
            "item_id": 11,
            "name": "test",
            "description": "test",
            "category": 2,
            "images_qty": 2,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["is_allowed"] is False

def test_predict_no_imgs(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 3,
            "is_verified_seller": False,
            "item_id": 12,
            "name": "test",
            "description": "test",
            "category": 3,
            "images_qty": 0,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["is_allowed"] is False


def test_predict_invalid_name_type(app_client: TestClient):
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


def test_predict_over_imgs(app_client: TestClient):
    response = app_client.post(
        "/predict",
        json={
            "seller_id": 3,
            "is_verified_seller": False,
            "item_id": 12,
            "name": "test",
            "description": "test",
            "category": 3,
            "images_qty": 11,
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Too many images"



import pytest
from unittest.mock import AsyncMock
from workers.moderation_worker import ModerationWorker
from repositories.users import user_repository
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository
from services.predict import PredictService, PredictionError, ModelNotLoadedError
from model import ensure_model_exists


@pytest.mark.asyncio
async def test_moderation_worker_process_message_success():
    user = await user_repository.create(
        seller_id=200,
        is_verified_seller=False
    )

    item = await item_repository.create(
        item_id=300,
        seller_id=user['seller_id'],
        name="Test Item",
        description="Test Description for moderation",
        category=50,
        images_qty=3
    )

    moderation_result = await moderation_result_repository.create(item['id'])
    moderation_id = moderation_result['id']

    worker = ModerationWorker()

    model = ensure_model_exists()
    worker.model = model
    worker.predict_service = PredictService(model=model)

    message = {
        "item_id": item['item_id'],
        "timestamp": "2024-01-15T10:30:45.123456"
    }

    await worker.process_message(message)

    updated_result = await moderation_result_repository.get_by_id(moderation_id)

    assert updated_result is not None
    assert updated_result['status'] == 'completed'
    assert updated_result['is_violation'] is not None
    assert updated_result['probability'] is not None
    assert isinstance(updated_result['is_violation'], bool)
    assert isinstance(updated_result['probability'], float)
    assert 0.0 <= updated_result['probability'] <= 1.0
    assert updated_result['processed_at'] is not None


@pytest.mark.asyncio
async def test_moderation_worker_process_message_item_not_found():
    worker = ModerationWorker()

    message = {
        "item_id": 99999,
        "timestamp": "2024-01-15T10:30:45.123456"
    }

    await worker.process_message(message)

@pytest.mark.asyncio
async def test_moderation_worker_process_message_moderation_not_found():
    user = await user_repository.create(
        seller_id=201,
        is_verified_seller=False
    )

    item = await item_repository.create(
        item_id=301,
        seller_id=user['seller_id'],
        name="Test Item",
        description="Test Description",
        category=50,
        images_qty=1
    )

    worker = ModerationWorker()
    model = ensure_model_exists()
    worker.model = model
    worker.predict_service = PredictService(model=model)

    message = {
        "item_id": item['item_id'],
        "timestamp": "2024-01-15T10:30:45.123456"
    }

    await worker.process_message(message)

@pytest.mark.asyncio
async def test_moderation_worker_process_message_prediction_error():
    user = await user_repository.create(
        seller_id=202,
        is_verified_seller=False
    )

    item = await item_repository.create(
        item_id=302,
        seller_id=user['seller_id'],
        name="Test Item",
        description="Test Description",
        category=50,
        images_qty=1
    )

    moderation_result = await moderation_result_repository.create(item['id'])
    moderation_id = moderation_result['id']

    worker = ModerationWorker()

    mock_predict_service = AsyncMock()
    mock_predict_service.predict = AsyncMock(side_effect=PredictionError("Test prediction error"))
    worker.predict_service = mock_predict_service

    message = {
        "item_id": item['item_id'],
        "timestamp": "2024-01-15T10:30:45.123456"
    }

    await worker.process_message(message)

    updated_result = await moderation_result_repository.get_by_id(moderation_id)

    assert updated_result is not None
    assert updated_result['status'] == 'failed'
    assert updated_result['error_message'] is not None
    assert "prediction error" in updated_result['error_message'].lower()
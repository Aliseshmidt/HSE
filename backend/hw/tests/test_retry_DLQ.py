import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from workers.moderation_worker import ModerationWorker, MAX_RETRY_COUNT, RETRY_DELAY_SECONDS
from repositories.users import user_repository
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository
from services.predict import ModelNotLoadedError, PredictService
from clients.kafka import KafkaProducer


@pytest.mark.asyncio
async def test_retry_mechanism():
    user = await user_repository.create(
        seller_id=500,
        is_verified_seller=False
    )

    item = await item_repository.create(
        item_id=600,
        seller_id=user['seller_id'],
        name="Test Retry Item",
        description="Test description for retry mechanism",
        category=50,
        images_qty=2
    )

    moderation_result = await moderation_result_repository.create(item['id'])
    moderation_id = moderation_result['id']

    worker = ModerationWorker()

    worker.model = None
    worker.predict_service = PredictService(model=None)

    mock_kafka_producer = AsyncMock()
    mock_kafka_producer.send_to_dlq = AsyncMock(return_value=None)
    worker.kafka_producer = mock_kafka_producer

    message = {
        "item_id": item['item_id'],
        "timestamp": "2025-02-04T12:00:00.123456"
    }

    start_time = asyncio.get_event_loop().time()

    await worker.process_message(message, retry_count=0)

    end_time = asyncio.get_event_loop().time()
    elapsed_time = end_time - start_time

    final_result = await moderation_result_repository.get_by_id(moderation_id)

    assert final_result is not None, "Запись модерации должна существовать"
    assert final_result['status'] == 'failed', f"Статус должен быть 'failed', получен: {final_result['status']}"
    assert final_result['error_message'] is not None, "Должно быть сообщение об ошибке"
    assert 'Модель не загружена' in final_result['error_message'], "Ошибка должна содержать информацию о модели"
    assert final_result['processed_at'] is not None, "Должно быть время обработки"

    mock_kafka_producer.send_to_dlq.assert_called_once()
    dlq_call_args = mock_kafka_producer.send_to_dlq.call_args
    assert dlq_call_args[1]['retry_count'] == MAX_RETRY_COUNT, f"retry_count должен быть {MAX_RETRY_COUNT}"

    expected_min_time = (MAX_RETRY_COUNT * RETRY_DELAY_SECONDS) - 2
    assert elapsed_time >= expected_min_time, f"Время выполнения должно быть не менее {expected_min_time} секунд, получено {elapsed_time:.2f}"


@pytest.mark.asyncio
async def test_retry_mechanism_max_attempts():
    user = await user_repository.create(
        seller_id=501,
        is_verified_seller=False
    )

    item = await item_repository.create(
        item_id=601,
        seller_id=user['seller_id'],
        name="Test Retry Item 2",
        description="Test",
        category=50,
        images_qty=1
    )

    moderation_result = await moderation_result_repository.create(item['id'])
    moderation_id = moderation_result['id']

    worker = ModerationWorker()
    worker.model = None
    worker.predict_service = PredictService(model=None)

    mock_kafka_producer = AsyncMock()
    mock_kafka_producer.send_to_dlq = AsyncMock(return_value=None)
    worker.kafka_producer = mock_kafka_producer

    message = {
        "item_id": item['item_id'],
        "timestamp": "2025-02-04T12:00:00.123456"
    }

    await worker.process_message(message, retry_count=0)

    final_result = await moderation_result_repository.get_by_id(moderation_id)
    assert final_result['status'] == 'failed'

    assert mock_kafka_producer.send_to_dlq.called
    call_kwargs = mock_kafka_producer.send_to_dlq.call_args[1]
    assert call_kwargs['retry_count'] == MAX_RETRY_COUNT
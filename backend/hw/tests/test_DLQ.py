import pytest
from clients.kafka import KafkaProducer


@pytest.mark.asyncio
async def test_send_to_dlq():
    producer = KafkaProducer()
    
    try:
        await producer.start()

        original_message = {
            "item_id": 999,
            "timestamp": "2025-02-04T12:00:00.123456"
        }

        await producer.send_to_dlq(
            original_message=original_message,
            error="Тестовое сообщение для создания топика DLQ",
            retry_count=0
        )

        
    except Exception as e:
        pytest.fail(f"Ошибка при отправке в DLQ: {e}")
    finally:
        await producer.stop()


@pytest.mark.asyncio
async def test_send_to_dlq_with_retry_count():
    producer = KafkaProducer()
    
    try:
        await producer.start()
        
        original_message = {
            "item_id": 1000,
            "timestamp": "2025-02-04T12:00:00.123456"
        }

        await producer.send_to_dlq(
            original_message=original_message,
            error="Тестовая ошибка после 3 попыток",
            retry_count=3
        )

        
    except Exception as e:
        pytest.fail(f"Ошибка при отправке в DLQ с retry_count: {e}")
    finally:
        await producer.stop()
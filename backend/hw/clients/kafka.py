import json
import logging
from datetime import datetime
from typing import Optional
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
MODERATION_TOPIC = "moderation"
MODERATION_DLQ_TOPIC = "moderation_dlq"


class KafkaProducer:
    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info(f"Kafka Producer запущен: {self.bootstrap_servers}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka Producer остановлен")

    async def send_moderation_request(self, item_id: int) -> None:
        if self.producer is None:
            await self.start()

        message = {
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await self.producer.send_and_wait(
                MODERATION_TOPIC,
                value=message
            )
            logger.info(f"Сообщение отправлено в Kafka для item_id={item_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Kafka для item_id={item_id}: {e}")
            raise

    async def send_to_dlq(self, original_message: dict, error: str, retry_count: int = 0) -> None:
        if self.producer is None:
            await self.start()

        dlq_message = {
            "original_message": original_message,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "retry_count": retry_count
        }

        try:
            await self.producer.send_and_wait(
                MODERATION_DLQ_TOPIC,
                value=dlq_message
            )
            logger.info(f"Сообщение отправлено в DLQ для item_id={original_message.get('item_id')}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в DLQ: {e}")
            raise

_kafka_producer: Optional[KafkaProducer] = None


async def get_kafka_producer() -> KafkaProducer:
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer()
        await _kafka_producer.start()
    return _kafka_producer


async def close_kafka_producer():
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.stop()
        _kafka_producer = None


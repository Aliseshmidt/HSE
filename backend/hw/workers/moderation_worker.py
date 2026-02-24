import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from database import db
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository
from services.predict import PredictService, PredictionError, ModelNotLoadedError
from model import ensure_model_exists
from clients.kafka import KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
MODERATION_TOPIC = "moderation"
CONSUMER_GROUP_ID = "moderation_worker_group"
MAX_RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 5


class ModerationWorker:
    def __init__(self):
        self.consumer: AIOKafkaConsumer = None
        self.model = None
        self.predict_service = None
        self.kafka_producer: KafkaProducer = None
        self.running = True

    async def initialize(self):
        try:
            await db.connect()
            logger.info("Подключение к БД установлено")

            self.model = ensure_model_exists()
            self.predict_service = PredictService(model=self.model)
            logger.info("Модель успешно загружена")

            self.kafka_producer = KafkaProducer()
            await self.kafka_producer.start()
            logger.info("Kafka Producer для DLQ запущен")

            self.consumer = AIOKafkaConsumer(
                MODERATION_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=CONSUMER_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            await self.consumer.start()
            logger.info(f"Kafka Consumer запущен. Подписка на топик: {MODERATION_TOPIC}")

        except Exception as e:
            logger.error(f"Ошибка при инициализации воркера: {e}")
            raise

    def _is_retryable_error(self, error: Exception) -> bool:
        if isinstance(error, ModelNotLoadedError):
            return True
        return False

    async def _send_to_dlq(self, original_message: dict, error: str, retry_count: int):
        item_id = original_message.get('item_id')
        
        try:
            await self.kafka_producer.send_to_dlq(
                original_message=original_message,
                error=error,
                retry_count=retry_count
            )
            logger.info(f"Сообщение отправлено в DLQ для item_id={item_id}")
        except Exception as dlq_error:
            logger.error(f"Ошибка при отправке в DLQ: {dlq_error}")

    async def process_message(self, message_value: dict, retry_count: int = 0):
        retry_count = message_value.get('retry_count', retry_count)
        
        item_id = message_value.get('item_id')
        if item_id is None:
            logger.error(f"Сообщение не содержит item_id: {message_value}")
            return

        logger.info(f"Получено сообщение для обработки: item_id={item_id}, retry_count={retry_count}")

        internal_item_id = None
        moderation_id = None
        error_message = None

        try:
            item = await item_repository.get_by_item_id(item_id)
            if item is None:
                error_message = f"Объявление с item_id={item_id} не найдено в БД"
                logger.error(error_message)
                await self._send_to_dlq(message_value, error_message, retry_count)
                return

            internal_item_id = item['id']

            moderation_result = await moderation_result_repository.get_latest_by_item_id(internal_item_id)
            if moderation_result is None:
                error_message = f"Запись модерации для item_id={internal_item_id} не найдена"
                logger.error(error_message)
                await self._send_to_dlq(message_value, error_message, retry_count)
                return

            moderation_id = moderation_result['id']

            is_violation, probability = await self.predict_service.predict(
                seller_id=item['seller_id'],
                is_verified_seller=item['is_verified_seller'],
                item_id=item['item_id'],
                name=item['name'],
                description=item['description'],
                category=item['category'],
                images_qty=item['images_qty']
            )

            await moderation_result_repository.update_status(
                moderation_id=moderation_id,
                status="completed",
                is_violation=is_violation,
                probability=probability
            )

            logger.info(
                f"Модерация завершена: moderation_id={moderation_id}, "
                f"item_id={item_id}, is_violation={is_violation}, probability={probability:.4f}"
            )

        except ModelNotLoadedError as e:
            error_message = f"Модель не загружена: {str(e)}"
            logger.error(error_message)

            if retry_count < MAX_RETRY_COUNT:
                logger.info(f"Повторная попытка {retry_count + 1}/{MAX_RETRY_COUNT} через {RETRY_DELAY_SECONDS} секунд")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

                message_value['retry_count'] = retry_count + 1
                await self.process_message(message_value, retry_count + 1)
                return
            else:
                logger.error(f"Превышено максимальное количество попыток ({MAX_RETRY_COUNT}) для item_id={item_id}")
                if moderation_id:
                    try:
                        await moderation_result_repository.update_status(
                            moderation_id=moderation_id,
                            status="failed",
                            error_message=error_message
                        )
                    except Exception as update_error:
                        logger.error(f"Ошибка при обновлении статуса: {update_error}")
                await self._send_to_dlq(message_value, error_message, retry_count)

        except PredictionError as e:
            error_message = f"Ошибка при предсказании: {str(e)}"
            logger.error(f"Ошибка при предсказании для item_id={item_id}: {e}")

            if moderation_id:
                try:
                    await moderation_result_repository.update_status(
                        moderation_id=moderation_id,
                        status="failed",
                        error_message=error_message
                    )
                except Exception as update_error:
                    logger.error(f"Ошибка при обновлении статуса: {update_error}")
            await self._send_to_dlq(message_value, error_message, retry_count)

        except Exception as e:
            error_message = f"Неожиданная ошибка: {str(e)}"
            logger.error(f"Неожиданная ошибка при обработке item_id={item_id}: {e}", exc_info=True)

            if self._is_retryable_error(e) and retry_count < MAX_RETRY_COUNT:
                logger.info(f"Повторная попытка {retry_count + 1}/{MAX_RETRY_COUNT} через {RETRY_DELAY_SECONDS} секунд")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

                message_value['retry_count'] = retry_count + 1
                await self.process_message(message_value, retry_count + 1)
                return
            else:
                if moderation_id:
                    try:
                        await moderation_result_repository.update_status(
                            moderation_id=moderation_id,
                            status="failed",
                            error_message=error_message
                        )
                    except Exception as update_error:
                        logger.error(f"Ошибка при обновлении статуса: {update_error}")
                await self._send_to_dlq(message_value, error_message, retry_count)

    async def run(self):
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    message_value = message.value
                    await self.process_message(message_value)
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)

        except asyncio.CancelledError:
            logger.info("Получен сигнал отмены, завершение работы...")
        except Exception as e:
            logger.error(f"Критическая ошибка в цикле обработки: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info("Завершение работы воркера...")
        self.running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka Consumer остановлен")

        if self.kafka_producer:
            await self.kafka_producer.stop()
            logger.info("Kafka Producer остановлен")

        await db.disconnect()
        logger.info("Подключение к БД закрыто")

    def setup_signal_handlers(self):
        def signal_handler(sig, frame):
            logger.info(f"Получен сигнал {sig}, завершение работы...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    worker = ModerationWorker()
    worker.setup_signal_handlers()

    try:
        await worker.initialize()
        logger.info("Воркер готов к обработке сообщений")
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())


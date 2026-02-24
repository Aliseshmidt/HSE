from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository
from clients.kafka import get_kafka_producer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/async_predict", tags=["async_predict"])


class AsyncPredictInDto(BaseModel):
    item_id: int


class AsyncPredictOutDto(BaseModel):
    task_id: int
    status: str
    message: str


@router.post("", response_model=AsyncPredictOutDto, status_code=status.HTTP_200_OK)
async def async_predict(dto: AsyncPredictInDto) -> AsyncPredictOutDto:
    item_id = dto.item_id

    item = await item_repository.get_by_item_id(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с item_id={item_id} не найдено"
        )

    internal_item_id = item['id']

    moderation_result = await moderation_result_repository.create(internal_item_id)
    task_id = moderation_result['id']

    try:
        kafka_producer = await get_kafka_producer()
        await kafka_producer.send_moderation_request(item_id)

        logger.info(
            f"Задача модерации создана: task_id={task_id}, item_id={item_id}"
        )

        return AsyncPredictOutDto(
            task_id=task_id,
            status="pending",
            message="Moderation request accepted"
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке в Kafka для item_id={item_id}: {e}")

        try:
            await moderation_result_repository.update_status(
                moderation_id=task_id,
                status="failed",
                error_message=f"Ошибка при отправке в Kafka: {str(e)}"
            )
        except Exception as update_error:
            logger.error(f"Ошибка при обновлении статуса записи {task_id}: {update_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании задачи модерации: {str(e)}"
        )


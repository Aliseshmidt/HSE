from http import HTTPStatus

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository
from prediction_storage import prediction_storage


router = APIRouter(prefix="", tags=["items"])


class CloseItemInDto(BaseModel):
    item_id: int


class CloseItemOutDto(BaseModel):
    item_id: int
    status: str


@router.post("/close", response_model=CloseItemOutDto, status_code=status.HTTP_200_OK)
async def close_item(dto: CloseItemInDto) -> CloseItemOutDto:
    item_id = dto.item_id

    item = await item_repository.get_by_item_id(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с item_id={item_id} не найдено",
        )

    internal_item_id = item["id"]

    task_ids = await moderation_result_repository.get_ids_by_item_internal_id(internal_item_id)

    await moderation_result_repository.delete_by_item_internal_id(internal_item_id)
    await item_repository.delete_by_item_id(item_id)

    await prediction_storage.delete_by_item_id(item_id)
    for task_id in task_ids:
        await prediction_storage.delete_by_task_id(task_id)

    return CloseItemOutDto(item_id=item_id, status="closed")


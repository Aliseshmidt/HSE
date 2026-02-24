from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from repositories.moderation_results import moderation_result_repository
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderation_result", tags=["moderation_result"])


class ModerationResultOutDto(BaseModel):
    task_id: int
    status: str
    is_violation: Optional[bool] = None
    probability: Optional[float] = None


@router.get("/{task_id}", response_model=ModerationResultOutDto, status_code=status.HTTP_200_OK)
async def get_moderation_result(task_id: int) -> ModerationResultOutDto:
    moderation_result = await moderation_result_repository.get_by_id(task_id)
    
    if moderation_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача модерации с task_id={task_id} не найдена"
        )

    return ModerationResultOutDto(
        task_id=moderation_result['id'],
        status=moderation_result['status'],
        is_violation=moderation_result['is_violation'],
        probability=moderation_result['probability']
    )


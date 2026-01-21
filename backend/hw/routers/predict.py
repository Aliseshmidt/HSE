from fastapi import APIRouter, HTTPException, status, Response, Request
from typing import Sequence
from pydantic import BaseModel
from services.predict import PredictService, PredictionError


router = APIRouter(prefix="/predict", tags=["predict"])

class PredictInDto(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int


class PredictOutDto(BaseModel):
    is_allowed: bool


predict_service = PredictService()


@router.post("", response_model=PredictOutDto, status_code=status.HTTP_200_OK)
async def predict(dto: PredictInDto) -> PredictOutDto:
    try:
        result = await predict_service.predict(
            is_verified_seller=dto.is_verified_seller,
            images_qty=dto.images_qty)
        return PredictOutDto(is_allowed=result)
    except PredictionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e))


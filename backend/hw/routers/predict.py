from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from services.predict import PredictService, PredictionError, ModelNotLoadedError

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
    is_violation: bool
    probability: float


def get_predict_service(request: Request) -> PredictService:
    model = getattr(request.app.state, 'model', None)
    service = PredictService(model=model)
    return service


@router.post("", response_model=PredictOutDto, status_code=status.HTTP_200_OK)
async def predict(dto: PredictInDto, request: Request) -> PredictOutDto:
    predict_service = get_predict_service(request)

    try:
        is_violation, probability = await predict_service.predict(
            seller_id=dto.seller_id,
            is_verified_seller=dto.is_verified_seller,
            item_id=dto.item_id,
            name=dto.name,
            description=dto.description,
            category=dto.category,
            images_qty=dto.images_qty
        )
        return PredictOutDto(
            is_violation=is_violation,
            probability=probability
        )
    except ModelNotLoadedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Модель не загружена'
        )
    except PredictionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при предсказании {str(e)}'
        )

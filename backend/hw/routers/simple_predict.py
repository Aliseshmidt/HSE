from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from services.predict import PredictService, PredictionError, ModelNotLoadedError
from repositories.items import item_repository

router = APIRouter(prefix="/simple_predict", tags=["simple_predict"])


class SimplePredictOutDto(BaseModel):
    is_violation: bool
    probability: float


def get_predict_service(request: Request) -> PredictService:
    model = getattr(request.app.state, 'model', None)
    service = PredictService(model=model)
    return service


@router.post("/{item_id}", response_model=SimplePredictOutDto, status_code=status.HTTP_200_OK)
async def simple_predict(item_id: int, request: Request) -> SimplePredictOutDto:
    item = await item_repository.get_by_item_id(item_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с item_id={item_id} не найдено"
        )

    predict_service = get_predict_service(request)

    try:
        is_violation, probability = await predict_service.predict(
            seller_id=item['seller_id'],
            is_verified_seller=item['is_verified_seller'],
            item_id=item['item_id'],
            name=item['name'],
            description=item['description'],
            category=item['category'],
            images_qty=item['images_qty']
        )
        return SimplePredictOutDto(
            is_violation=is_violation,
            probability=probability
        )
    except ModelNotLoadedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Модель не загружена'
        )
    except PredictionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при предсказании {str(e)}'
        )
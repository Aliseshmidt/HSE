import numpy as np
import logging
import time
from typing import Tuple

from app.metrics import (
    MODEL_PREDICTION_PROBABILITY,
    PREDICTION_DURATION_SECONDS,
    PREDICTION_ERRORS_TOTAL,
    PREDICTIONS_TOTAL,
)

logger = logging.getLogger(__name__)


class PredictionError(Exception):
    pass


class ModelNotLoadedError(Exception):
    pass


class PredictService:
    def __init__(self, model=None):
        self.model = model

    def set_model(self, model):
        self.model = model

    def _prepare_features(self, is_verified_seller: bool, images_qty: int, description_length: int,
                          category: int) -> np.ndarray:
        features = np.array([[
            1.0 if is_verified_seller else 0.0,
            images_qty / 10,
            description_length / 1000,
            category / 100
        ]])
        return features

    async def predict(self, seller_id: int, is_verified_seller: bool, item_id: int, name: str, description: str, category: int, images_qty: int) -> Tuple[bool, float]:
        if self.model is None:
            PREDICTION_ERRORS_TOTAL.labels(error_type="model_unavailable").inc()
            raise ModelNotLoadedError("Модель не загружена")

        try:
            logger.info(
                f"Запрос предсказания: seller_id={seller_id}, item_id={item_id}, "
                f"is_verified_seller={is_verified_seller}, images_qty={images_qty}, "
                f"description_length={len(description)}, category={category}"
            )

            features = self._prepare_features(
                is_verified_seller=is_verified_seller,
                images_qty=images_qty,
                description_length=len(description),
                category=category
            )

            t0 = time.perf_counter()
            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0][1]
            PREDICTION_DURATION_SECONDS.observe(time.perf_counter() - t0)

            is_violation = bool(prediction)
            PREDICTIONS_TOTAL.labels(
                result="violation" if is_violation else "no_violation"
            ).inc()
            MODEL_PREDICTION_PROBABILITY.observe(float(probability))

            logger.info(
                f"Результат предсказания: seller_id={seller_id}, item_id={item_id}, "
                f"is_violation={is_violation}, probability={probability:.4f}"
            )

            return is_violation, float(probability)

        except Exception as e:
            PREDICTION_ERRORS_TOTAL.labels(error_type="prediction_error").inc()
            logger.error(f"Ошибка при предсказании: {e}")
            raise PredictionError(f"Ошибка при предсказании: {str(e)}")
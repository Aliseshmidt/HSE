class PredictionError(Exception):
    pass


class PredictService:
    async def predict(self, is_verified_seller: bool, images_qty: int) -> bool:
        if images_qty > 10:
            raise PredictionError("Too many images")

        if is_verified_seller:
            return images_qty > 0
        else:
            return False

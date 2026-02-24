from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.predict import router as predict_router
from routers.simple_predict import router as simple_predict_router
from routers.async_predict import router as async_predict_router
from routers.moderation_result import router as moderation_result_router
from model import ensure_model_exists
from database import db
from clients.kafka import close_kafka_producer
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        model = ensure_model_exists()
        app.state.model = model
        logger.info("Модель успешно загружена")
    except Exception as e:
        logger.error(f"Ошибка при загрузке модели: {e}")
        app.state.model = None

    try:
        await db.connect()
        logger.info("Подключение к БД установлено")
    except Exception as e:
        logger.error(f"Ошибка при подключении к БД: {e}")
        raise

    yield

    await close_kafka_producer()
    await db.disconnect()
    logger.info("Завершение работы сервиса")


app = FastAPI(lifespan=lifespan)
app.include_router(predict_router)
app.include_router(simple_predict_router)
app.include_router(async_predict_router)
app.include_router(moderation_result_router)


@app.get("/")
async def root():
    return {'message': 'Hello World'}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
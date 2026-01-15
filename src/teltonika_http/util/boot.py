from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.teltonika_http.config import settings
from src.teltonika_http.infra.broker.redis_client import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # инициализация один раз при старте
    app.state.broker = RedisClient(settings.redis_url, decode_responses=False)
    try:
        # можно сделать ping/ensure_connected здесь
        await app.state.broker.connect()
        await app.state.broker.ping()
        yield
    finally:
        # корректное закрытие при завершении
        await app.state.broker.shutdown()

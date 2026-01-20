from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.teltonika_http.config import settings
from src.teltonika_http.infra.broker.redis_client import RedisClient
from src.teltonika_http.infra.db.exceptions import AppError


logger = logging.getLogger()


async def error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        # логирование
        logger.exception("Unhandled error", exc_info=exc)

        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        )
    

async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "path": request.url.path
        }
    )
    

async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "VALUE_ERROR",
            "message": str(exc),
            "path": request.url.path
        }
    )


def register_middlewares(app: FastAPI):
    app.middleware("http")(error_middleware)


def register_exception_handlers(app: FastAPI):
    app.exception_handler(ValueError)(value_error_handler)
    app.exception_handler(AppError)(app_error_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # инициализация один раз при старте
    app.state.broker = RedisClient(settings.redis_url, decode_responses=True)
    try:
        # можно сделать ping/ensure_connected здесь
        await app.state.broker.connect()
        await app.state.broker.ping()
        yield
    finally:
        # корректное закрытие при завершении
        await app.state.broker.shutdown()


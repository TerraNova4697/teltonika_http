import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .routes import admin, auth, users, transport, connection

from src.teltonika_http.config import initial_setup
from src.teltonika_http.util.boot import lifespan, register_exception_handlers, register_middlewares


initial_setup()


logger = logging.getLogger()


app = FastAPI(lifespan=lifespan)


register_middlewares(app)
register_exception_handlers(app)


app.include_router(router=admin.router)
app.include_router(router=auth.router)
app.include_router(router=users.router)
app.include_router(router=transport.router)
app.include_router(router=connection.router)

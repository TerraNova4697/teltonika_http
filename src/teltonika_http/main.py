import logging

from fastapi import FastAPI
from .routes import admin, auth, users, transport, connection

from src.teltonika_http.config import initial_setup
from src.teltonika_http.util.boot import lifespan


initial_setup()

logger = logging.getLogger()


app = FastAPI(lifespan=lifespan)


app.include_router(router=admin.router)
app.include_router(router=auth.router)
app.include_router(router=users.router)
app.include_router(router=transport.router)
app.include_router(router=connection.router)

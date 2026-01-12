import logging

from fastapi import FastAPI
from .routes import admin, auth, users, transport

from src.teltonika_http.config import initial_setup


initial_setup()

logger = logging.getLogger()


app = FastAPI()


app.include_router(router=admin.router)
app.include_router(router=auth.router)
app.include_router(router=users.router)
app.include_router(router=transport.router)

import logging

from fastapi import FastAPI
from .routes import admin, auth, users


logger = logging.getLogger()


app = FastAPI()


app.include_router(router=admin.router)
app.include_router(router=auth.router)
app.include_router(router=users.router)

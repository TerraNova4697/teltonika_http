from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.teltonika_http.infra.db.db import sessionmaker, session
from src.teltonika_http.infra.broker.redis_client import RedisClient
from src.teltonika_http.services.broker import BrokerService


def __get_db():
    return session


db_dep = Annotated[sessionmaker, Depends(__get_db)]


token_form_dep = Annotated[OAuth2PasswordRequestForm, Depends()]


token_dep = Annotated[str, Depends()]


async def get_broker(request: Request):
    return request.app.state.broker


broker_dep = Annotated[RedisClient, Depends(get_broker)]


async def get_broker_service(broker: broker_dep):
    return BrokerService(broker)


broker_service_dep = Annotated[BrokerService, Depends(get_broker_service)]

import logging

from fastapi import APIRouter

from src.teltonika_http.services.connection import ConnectionService
from src.teltonika_http.util.dependencies import db_dep, broker_service_dep
from src.teltonika_http.services.auth import current_user_dep
from src.teltonika_http.util.dtos import ConnectionListDto, ConnectionDto


logger = logging.getLogger("TransportRouter")


router = APIRouter(
    prefix="/connections",
    tags=["connections"],
)


@router.get("/", response_model=ConnectionListDto)
async def get_all(
    db: db_dep,
    broker: broker_service_dep,
    _: current_user_dep,
    page_size: int,
    offset: int,
):
    res = await ConnectionService(db, broker).get_all(page_size, offset)
    return res
    

@router.get("/by-imei/{imei}", response_model=ConnectionDto)
async def read_connection(
    broker: broker_service_dep,
    _: current_user_dep,
    imei: str
) -> ConnectionDto:
    res = await broker.get_connection_details(imei)
    return ConnectionDto.model_validate(res)
    
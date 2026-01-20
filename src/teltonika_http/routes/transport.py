from fastapi import APIRouter, HTTPException, Response, status
import logging

from src.teltonika_http.services.transport import TransportService
from src.teltonika_http.util.dependencies import db_dep
from src.teltonika_http.services.auth import current_user_dep
from src.teltonika_http.util.dtos import TransportDto, TransportListDto


logger = logging.getLogger("TransportRouter")


router = APIRouter(
    prefix="/transports",
    tags=["transports"],
)


@router.get("/by-imei/{imei}")
async def read_transport(
    imei: str, 
    db: db_dep,
    _: current_user_dep
):
    return await TransportService(db) \
        .get_details(imei)


@router.post("/", response_model=TransportDto)
async def create_transport(
    db: db_dep,
    transport: TransportDto,
    _: current_user_dep
):
    await TransportService(db).create(transport)

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/", response_model=TransportListDto)
async def get_all(
    db: db_dep,
    _: current_user_dep,
    page_size: int,
    page_num: int,
):
    return await TransportService(db).get_all(page_size, page_num)

from fastapi import APIRouter, HTTPException, Response, status
import logging

from src.teltonika_http.services.transport import TransportService
from src.teltonika_http.util.dependencies import db_dep
from src.teltonika_http.services.auth import current_user_dep
from src.teltonika_http.infra.db.exceptions import (
    ItemNotFoundException, 
    ItemExistsException,
    ParameterError
)
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
    try:
        result = await TransportService(db) \
            .get_details(imei)
    except ItemNotFoundException:
        raise HTTPException(status_code=404, detail="Transport not found")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
        
    return result

@router.post("/", response_model=TransportDto)
async def create_transport(
    db: db_dep,
    transport: TransportDto,
    _: current_user_dep
):
    try:
        await TransportService(db).create(transport)
    except ItemExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Entity exists"
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/", response_model=TransportListDto)
async def get_all(
    db: db_dep,
    _: current_user_dep,
    page_size: int,
    page_num: int,
):
    try:
        res = await TransportService(db).get_all(page_size, page_num)
        return res
    except ParameterError as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")

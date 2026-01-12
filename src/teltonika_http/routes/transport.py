from fastapi import APIRouter, HTTPException, Response, status

from src.teltonika_http.services.transport import TransportService
from src.teltonika_http.util.dependencies import db_dep
from src.teltonika_http.services.auth import current_user_dep
from src.teltonika_http.infra.db.exceptions import (
    ItemNotFoundException, 
    ItemExistsException
)
from src.teltonika_http.util.dtos import TransportDto


router = APIRouter(
    prefix="/transports",
    tags=["transports"],
)


@router.get("/{imei}")
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

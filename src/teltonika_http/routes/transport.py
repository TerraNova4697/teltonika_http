from fastapi import APIRouter, HTTPException

from src.teltonika_http.services.transport import TransportService
from src.teltonika_http.util.dependencies import db_dep


router = APIRouter(
    prefix="/transports",
    tags=["transports"],
)


@router.get("/{imei}")
async def read_transport(imei: str, db: db_dep):
    result = await TransportService(db) \
        .get_details(imei)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Transport not found")
        
    return result
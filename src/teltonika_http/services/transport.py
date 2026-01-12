from .base import BaseService
from ..infra.db.queries.transport_orm import TransportOrm
from ..infra.db.exceptions import ItemNotFoundException
from src.teltonika_http.util.dtos import TransportDto


class TransportService(BaseService):

    def __init__(self, db_session):
        super().__init__(db_session, "transport_service")
        self.db_orm = TransportOrm

    async def get_details(self, imei: str):
        item = self.db_orm().get_first(self.db, imei=imei)
        if not item:
            raise ItemNotFoundException
        return TransportDto.model_validate(item)
    
    async def create(self, transport: TransportDto):
        self.logger.info(transport.model_dump())
        self.db_orm().create(self.db, **transport.model_dump())
        
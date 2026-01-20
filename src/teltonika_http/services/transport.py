from .base import BaseService
from ..infra.db.queries.transport_orm import TransportOrm
from ..infra.db.exceptions import ItemNotFoundException
from src.teltonika_http.util.dtos import TransportDto, TransportListDto


class TransportService(BaseService):

    def __init__(self, db_session):
        super().__init__(db_session, "TransportService")
        self.db_orm = TransportOrm

    async def get_details(self, imei: str):
        item = self.db_orm().get_first(self.db, imei=imei)
        if not item:
            raise ItemNotFoundException
        return TransportDto.model_validate(item, from_attributes=True)
    
    async def create(self, transport: TransportDto):
        self.logger.info(transport.model_dump())
        self.db_orm().create(self.db, **transport.model_dump())

    async def get_all(self, page_size: int, page_num: int) -> TransportListDto:
        self.logger.info("Getting transport list")
        
        return self.db_orm().all_paginate(self.db, page_size, page_num)
        
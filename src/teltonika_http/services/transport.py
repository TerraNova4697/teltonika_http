from .base import BaseService
from ..infra.db.queries.transport_orm import TransportOrm


class TransportService(BaseService):

    def __init__(self, db_session):
        super().__init__(db_session, "transport_service")
        self.db_orm = TransportOrm

    async def get_details(self, imei: str):
        return {"imei": imei}
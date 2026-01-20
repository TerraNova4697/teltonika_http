from datetime import datetime
import logging

from src.teltonika_http.infra.broker.redis_client import RedisClient
from src.teltonika_http.config import settings


logger = logging.getLogger("BrokerService")


class BrokerService:
    def __init__(self, broker: RedisClient):
        self._broker = broker
        self._prefix = "connection"

    async def get_connections(self, imei_list: list[str]):
        logger.debug(f"requesting {imei_list} if exists: {self._prefix}")
        return await self._broker.keys_exist(
            [f"{self._prefix}:{imei}" for imei in imei_list]
        )

    async def remove_connection(self, imei: str):
        return await self._broker.delete(f"{self._prefix}:{imei}")
    
    async def get_connection_details(self, imei: str):
        return await self._broker.hgetall(f"{self._prefix}:{imei}")
    
    async def connection_exists(self, imei: str) -> bool:
        ...

    async def update_last_seen(self, imei: str):
        ts_now = datetime.timestamp(datetime.now())
        await self._broker.hset_kv(
            f"{self._prefix}:{imei}",
            "last_seen",
            ts_now
        )
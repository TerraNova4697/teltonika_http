import logging

from .base import BaseService
from ..infra.db.queries.transport_orm import TransportOrm
from src.teltonika_http.util.dtos import ConnectionListDto


logger = logging.getLogger("ConnectionService")


class ConnectionService(BaseService):

    def __init__(self, db_session, broker):
        super().__init__(db_session, broker=broker, logger_name="ConnectionService")
        self.db_orm = TransportOrm
    
    async def get_all(
        self,
        page_size: int,
        offset: int,
    ) -> ConnectionListDto:
        try:
            db_page_size = page_size
            db_page_offset = offset
            connections = []
            # Get records of transport from DB
            item_offset_list = self.db_orm().all_offset(
                self.db, db_page_size, db_page_offset
            )

            logger.debug(f"Data from DB ({len(item_offset_list.data)} items): {item_offset_list.data}")

            # Filter given recods by connection status
            active_connections = await self.broker.get_connections(
                [tr.imei for tr in item_offset_list.data]
            )

            logger.debug(f"Data from Redis ({len(active_connections)} items): {active_connections}")

            # Save all active connections by it's IMEI
            for transport, is_active in zip(item_offset_list.data, active_connections):
                logger.debug(f"Result after initial request: {transport.imei=}, {is_active=}")
                if is_active:
                    connections.append(transport.imei)

            # Iterate until connections == page size or records end
            logger.debug(f"Should iterate in while? {len(connections) < page_size}, {item_offset_list.has_next}")
            while len(connections) < page_size and item_offset_list.has_next:
                db_page_size = page_size - len(connections)
                db_page_offset = item_offset_list.offset
                logger.debug(f"while iteration: {db_page_size=}, {db_page_offset=}")

                # Get records of transport from DB
                item_offset_list = self.db_orm().all_offset(
                    self.db, db_page_size, db_page_offset
                )

                logger.debug(f"{item_offset_list.data}")

                # Filter given recods by connection status
                active_connections = await self.broker.get_connections(
                    [tr.imei for tr in item_offset_list.data]
                )

                logger.debug(f"{active_connections}")

                # Save all active connections by it's IMEI
                for transport, is_active in zip(item_offset_list.data, active_connections):
                    if is_active:
                        connections.append(transport.imei)

            return ConnectionListDto(
                data=connections,
                offset=item_offset_list.offset
            )

        except Exception as e:
            self._handle_error(e)

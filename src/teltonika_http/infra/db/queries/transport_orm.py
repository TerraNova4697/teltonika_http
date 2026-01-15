from typing import Callable
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .base_orm import BaseOrm
from ..models import Transport
from src.teltonika_http.util.dtos import ItemListOffsetDto, TransportDto


logger = logging.getLogger("TransportOrm")


class TransportOrm(BaseOrm):

    def __init__(self):
        super().__init__(Transport, TransportDto)

    def all_offset(
        self, session_factory: Callable[[], Session], page_size: int, offset: int
    ) -> ItemListOffsetDto:
        with session_factory() as session:
            if page_size <= 0:
                raise ValueError("page_size must be > 0")
            if offset < 0:
                raise ValueError("page_num must be >= 0")

            # Count items
            total_items = session.execute(
                select(func.count())
                .select_from(self.model)
            ).scalar_one()

            query = (
                select(self.model)
                .offset(offset)
                .limit(page_size)
            )

            res = session.execute(query).scalars().all()

            logger.debug(f"Items got: {len(res)}, {offset=}, {total_items=}")
            has_next = len(res) + offset < total_items
            logger.debug(f"Does DB have more records? {has_next=}")

            return ItemListOffsetDto(
                data=[self._dto.model_validate(item, from_attributes=True) for item in res],
                total_elements=total_items,
                offset=offset + len(res),
                has_next=has_next
            )
         

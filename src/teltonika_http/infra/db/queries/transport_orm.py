from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .base_orm import BaseOrm
from ..db import session
from ..models import Transport


class TransportOrm(BaseOrm):

    def __init__(self):
        super().__init__(Transport)

    def all() -> list[Transport]:
        with session() as s:
            return s.execute(
                select(Transport) \
                    .options(joinedload(Transport.sensors))
            ).unique().scalars().all()


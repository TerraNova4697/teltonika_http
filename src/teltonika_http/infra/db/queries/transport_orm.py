from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..db import session
from ..models import Transport


class TransportOrm:

    @staticmethod
    def all() -> list[Transport]:
        with session() as s:
            return s.execute(
                select(Transport) \
                    .options(joinedload(Transport.sensors))
            ).unique().scalars().all()

    @staticmethod
    def get_first(session_factory, **kwargs) -> Transport:
        with session_factory() as session:
            query = select(Transport)
            for k, v in kwargs.items():
                if hasattr(Transport, k):
                    query = query.where(getattr(Transport, k) == v)

            return session.execute(query).scalars().first()

    @staticmethod
    def create(**kwargs):
        with session() as s:
            tr = Transport(**kwargs)
            s.add(tr)
            s.flush()
            s.commit()

    @staticmethod
    def delete(transport: Transport):
        with session() as s:
            s.delete(transport)
            s.commit()

    @staticmethod
    def update(transport: Transport):
        with session() as s:
            s.add(transport)
            s.commit()

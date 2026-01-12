from abc import ABC

from sqlalchemy import select, update, delete

from ..db import Base


class BaseOrm(ABC):
    def __init__(self, model: Base):
        self.model = model

    def get_first(self, session_factory, **kwargs) -> Base:
        with session_factory() as session:
            query = select(self.model)
            for k, v in kwargs.items():
                if hasattr(self.model, k):
                    query = query.where(getattr(self.model, k) == v)

            return session.execute(query).scalars().first()
        
    def create(self, session, **kwargs):
        with session() as s:
            tr = self.model(**kwargs)
            s.add(tr)
            s.flush()
            s.commit()

    def update(self, session, entity_id: int, **values):
        with session() as s:
            stmt = (
                update(self.model)
                .where(self.model.id == entity_id)
                .values(**values)
                .execution_options(synchronize_session="fetch")
            )
            s.execute(stmt)
            s.commit()

    def delete(self, session, entity_id: int):
        with session() as s:
            stmt = (
                delete(self.model)
                .where(self.model.id == entity_id)
                .execution_options(synchronize_session="fetch")
            )
            s.execute(stmt)
            s.commit()

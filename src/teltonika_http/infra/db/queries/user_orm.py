from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..db import session
from ..models import UserModel


class UserOrm:

    @staticmethod
    def all() -> list[UserModel]:
        with session() as s:
            return s.execute(
                select(UserModel) \
                    .options(joinedload(UserModel.sensors))
            ).unique().scalars().all()
        
    @staticmethod
    def get_first(session_factory, **kwargs) -> UserModel:
        with session_factory() as session:
            query = select(UserModel)
            for k, v in kwargs.items():
                if hasattr(UserModel, k):
                    query = query.where(getattr(UserModel, k) == v)

            return session.execute(query).scalars().first()


    @staticmethod
    def create(session, **kwargs):
        with session() as s:
            tr = UserModel(**kwargs)
            s.add(tr)
            s.flush()
            s.commit()

    @staticmethod
    def delete(user: UserModel):
        with session() as s:
            s.delete(user)
            s.commit()

    @staticmethod
    def update(user: UserModel):
        with session() as s:
            s.add(user)
            s.commit()

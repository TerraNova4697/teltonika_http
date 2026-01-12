from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .base_orm import BaseOrm
from ..db import session
from ..models import UserModel


class UserOrm(BaseOrm):

    def __init__(self):
        super().__init__(UserModel)

    def all() -> list[UserModel]:
        with session() as s:
            return s.execute(
                select(UserModel)
            ).unique().scalars().all()

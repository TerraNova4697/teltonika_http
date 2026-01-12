from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import logging

from src.teltonika_http.config import settings


logger = logging.getLogger()


class DbCredentials():

    @property
    def url(self):
        return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:" \
            f"5432/{settings.POSTGRES_DB}"

db_creds = DbCredentials()

engine = create_engine(db_creds.url)

session = sessionmaker(engine)


class Base(DeclarativeBase):

    repr_cols_num = 3
    repr_cols = tuple()
    
    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"

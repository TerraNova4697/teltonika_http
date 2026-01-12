from abc import ABC
import functools
import logging

from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..db import Base
from ..exceptions import RepositoryError, ItemExistsException, AppError


logger = logging.getLogger("Database")


def handle_db_errors(func):
    @functools.wraps(func)
    def wrapper(self, session_factory, *args, **kwargs):
        try:
            return func(self, session_factory, *args, **kwargs)
        except AppError:
            raise
        except SQLAlchemyError as e:
            model_name = getattr(self, "model", Base).__name__
            logger.error(f"Database error in {model_name}.{func.__name__}: {e}")
            
            # Throwing app error
            raise RepositoryError(f"Data layer error in {func.__name__}")
        except Exception as e:
            logger.critical(f"Unexpected error in repository: {e}")
            raise RepositoryError("Internal repository failure")
    return wrapper


class BaseOrm(ABC):
    LOGGER = "Database"

    def __init__(self, model: Base):
        self.model = model
        self.logger = logging.getLogger("Database")

    @handle_db_errors
    def get_first(self, session_factory, **kwargs) -> Base:
        with session_factory() as session:
            query = select(self.model)
            for k, v in kwargs.items():
                if hasattr(self.model, k):
                    query = query.where(getattr(self.model, k) == v)

            return session.execute(query).scalars().first()
        
    @handle_db_errors
    def create(self, session_factory, **kwargs):
        with session_factory() as s:
            try:
                tr = self.model(**kwargs)
                s.add(tr)
                s.flush()
                s.commit()
            except IntegrityError:
                raise ItemExistsException

    @handle_db_errors
    def update(self, session_factory, entity_id: int, **values):
        with session_factory() as s:
            stmt = (
                update(self.model)
                .where(self.model.id == entity_id)
                .values(**values)
                .execution_options(synchronize_session="fetch")
            )
            s.execute(stmt)
            s.commit()

    @handle_db_errors
    def delete(self, session_factory, entity_id: int):
        with session_factory() as s:
            stmt = (
                delete(self.model)
                .where(self.model.id == entity_id)
                .execution_options(synchronize_session="fetch")
            )
            s.execute(stmt)
            s.commit()

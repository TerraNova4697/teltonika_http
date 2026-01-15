from abc import ABC
import functools
import logging
from math import ceil
from typing import Callable

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db import Base
from ..exceptions import RepositoryError, ItemExistsException, AppError
from src.teltonika_http.util.dtos import ItemListPageDto


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

    def __init__(self, model: type[Base], dto: type[BaseModel] = None):
        self.model: type[Base] = model
        self._dto: type[BaseModel] = dto
        self.logger = logging.getLogger("Database")

    def all_paginate(
            self, session_factory: Callable[[], Session], page_size, page_num, **kwargs
    ) -> ItemListPageDto:
        if page_size <= 0:
            raise ValueError("page_size must be > 0")
        if page_num < 0:
            raise ValueError("page_num must be >= 0")
        
        offset = page_size * page_num
        
        with session_factory() as s:

            # Build the SQL query with given params in kwargs
            query = (
                select(func.count()).select_from(self.model)
            )
            for k, v in kwargs.items():
                if hasattr(self.model, k):
                    query = query.where(getattr(self.model, k) == v)

            # Getting total items and total pages
            total_items = s.execute(query).scalar_one()
            total_pages = ceil(total_items / page_size) if total_items else 0

            # Building the main query itself
            query = (
                select(self.model).offset(offset).limit(page_size)
            )
            for k, v in kwargs.items():
                if hasattr(self.model, k):
                    query = query.where(getattr(self.model, k) == v)

            items = s.execute(query).scalars().all()

            has_next = page_num + 1 < total_pages

            return ItemListPageDto(
                data=[self._dto.model_validate(item, from_attributes=True) for item in items],
                total_pages=total_pages,
                total_elements=total_items,
                has_hext=has_next
            )

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

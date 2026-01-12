from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..db import session
from ..models import Transport, Sensor


class SensorOrm:

    @staticmethod
    def all() -> list[Sensor]:
        with session() as s:
            return s.execute(
                select(Sensor)
            ).unique().scalars().all()

    @staticmethod
    def create(**kwargs):
        with session() as s:
            sens = Sensor(**kwargs)
            s.add(sens)
            s.flush()
            s.commit()

    @staticmethod
    def delete(sensor: Sensor):
        with session() as s:
            s.delete(sensor)
            s.commit()

    @staticmethod
    def update(sensor: Sensor):
        with session() as s:
            s.add(sensor)
            s.commit()


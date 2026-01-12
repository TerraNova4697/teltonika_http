from datetime import datetime, timezone
import enum
from typing import Annotated

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import String, ForeignKey, BigInteger, text, Boolean

from .db import Base


intpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime, mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.now(timezone.utc),
    )]



class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    email: Mapped[str] = mapped_column(String(length=255), unique=True)
    username: Mapped[str] = mapped_column(String(length=32), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(length=255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class SensorNumber(enum.Enum):
    one = 1
    two = 2
    three = 3
    four = 4


class SensorStatus(enum.Enum):
    attached = "attached"
    detached = "detached"


class Transport(Base):
    __tablename__ = "transports"

    imei: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(), nullable=True)
    sensors: Mapped[list["Sensor"]] = relationship(
        "Sensor",
        back_populates="transport",
    )


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(250))
    virtual_device_name: Mapped[str] = mapped_column(String(124))
    address: Mapped[str] = mapped_column(String(20), nullable=True)
    pin: Mapped[str] = mapped_column(String(6), nullable=True)
    transport_imei: Mapped[str] = mapped_column(ForeignKey("transports.imei", ondelete="CASCADE"))
    transport: Mapped["Transport"] = relationship("Transport", back_populates="sensors")
    sensor_num: Mapped["SensorNumber"]
    status: Mapped["SensorStatus"]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now(), nullable=True)

from __future__ import annotations

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from .enums import Continent


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(10), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    continent: Mapped[Continent] = mapped_column(Enum(Continent), default=Continent.INTERNATIONAL)
    flag: Mapped[str | None] = mapped_column(String(500), nullable=True)

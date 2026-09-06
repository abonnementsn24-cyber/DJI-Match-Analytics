from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .enums import CompetitionType, Continent, DataQuality

if TYPE_CHECKING:
    from .country import Country


class Competition(Base):
    """A competition as known to us — normalized, provider-agnostic.

    ``provider`` + ``provider_id`` identify where it came from (see
    ``ProviderCompetitionMapping`` for the general many-providers case);
    everything else is our own canonical view of it.
    """

    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider: Mapped[str] = mapped_column(String(64))
    provider_id: Mapped[str] = mapped_column(String(64))
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    canonical_name: Mapped[str] = mapped_column(String(255), index=True)
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"), nullable=True)
    continent: Mapped[Continent] = mapped_column(Enum(Continent), default=Continent.INTERNATIONAL)
    competition_type: Mapped[CompetitionType] = mapped_column(
        Enum(CompetitionType), default=CompetitionType.LEAGUE
    )
    tier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(16), default="MALE")

    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(default=True)

    data_quality: Mapped[DataQuality] = mapped_column(Enum(DataQuality), default=DataQuality.D)
    historical_depth: Mapped[int] = mapped_column(Integer, default=0)

    last_sync: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    country: Mapped[Country] = relationship()
    seasons: Mapped[list[Season]] = relationship(back_populates="competition")

    __table_args__ = ()


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    provider_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    year_start: Mapped[int] = mapped_column(Integer)
    year_end: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    end_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    current: Mapped[bool] = mapped_column(default=False)

    competition: Mapped[Competition] = relationship(back_populates="seasons")

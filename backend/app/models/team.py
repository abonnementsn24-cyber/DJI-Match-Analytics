from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .enums import TeamType

if TYPE_CHECKING:
    from .country import Country


class Team(Base):
    """A canonical team. The same club can be known under different names
    across providers (``ProviderTeamMapping`` resolves that); this row is
    our single source of truth for it.
    """

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(255), index=True)
    short_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"), nullable=True)
    founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_type: Mapped[TeamType] = mapped_column(Enum(TeamType), default=TeamType.CLUB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    country: Mapped[Country] = relationship()


class CompetitionSeasonTeam(Base):
    """Which team took part in which competition/season — a team can move
    divisions (or between competitions) from one season to the next."""

    __tablename__ = "competition_season_teams"
    __table_args__ = (UniqueConstraint("season_id", "team_id", name="uq_season_team"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

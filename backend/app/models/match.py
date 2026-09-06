from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .enums import MatchStatus, MatchWinner

if TYPE_CHECKING:
    from .competition import Competition
    from .team import Team


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("provider", "provider_id", name="uq_match_provider"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    provider_id: Mapped[str] = mapped_column(String(64))

    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)

    utc_date: Mapped[datetime.datetime] = mapped_column(DateTime, index=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)
    matchday: Mapped[int | None] = mapped_column(Integer, nullable=True)

    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winner: Mapped[MatchWinner | None] = mapped_column(Enum(MatchWinner), nullable=True)

    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    competition: Mapped[Competition] = relationship()
    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])

    @property
    def is_finished(self) -> bool:
        return self.status == MatchStatus.FINISHED and self.home_goals is not None

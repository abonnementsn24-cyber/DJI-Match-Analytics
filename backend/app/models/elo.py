from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class EloHistory(Base):
    """One row per (team, match): the Elo rating immediately before and
    after that match. This is what a historical prediction must read from
    — never the team's *current* rating — so replaying the past never
    leaks future information into it.
    """

    __tablename__ = "elo_history"
    __table_args__ = (UniqueConstraint("team_id", "match_id", name="uq_elo_team_match"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    rating_before: Mapped[float] = mapped_column(Float)
    rating_after: Mapped[float] = mapped_column(Float)
    date: Mapped[datetime.datetime] = mapped_column(DateTime, index=True)

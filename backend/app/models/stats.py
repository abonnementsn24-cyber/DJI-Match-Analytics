from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class TeamMatchStats(Base):
    """Optional in-match statistics. Not every provider/competition exposes
    these — columns stay nullable and the analytics layer treats a missing
    value as "unknown", never as zero.
    """

    __tablename__ = "team_match_stats"
    __table_args__ = (UniqueConstraint("match_id", "team_id", name="uq_match_team_stats"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))

    possession: Mapped[float | None] = mapped_column(Float, nullable=True)
    shots: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_on_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fouls: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yellow_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    red_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_goals: Mapped[float | None] = mapped_column(Float, nullable=True)

from __future__ import annotations

import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from .enums import Confidence, Outcome


class Prediction(Base):
    """A single model's prediction for a single match.

    Immutability contract (see docs/DATA_PIPELINE.md): once ``locked`` is
    true (set the moment the match kicks off), the probability/expected-goals
    columns are never written again. Only the evaluation columns
    (``actual_result``, ``correct``, ``brier_score``, ``log_loss``) are
    updated after the match finishes.
    """

    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint("match_id", "model_name", "model_version", name="uq_prediction_model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(64), index=True)
    model_version: Mapped[str] = mapped_column(String(32))
    generated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)

    home_win_probability: Mapped[float] = mapped_column(Float)
    draw_probability: Mapped[float] = mapped_column(Float)
    away_win_probability: Mapped[float] = mapped_column(Float)
    expected_home_goals: Mapped[float] = mapped_column(Float)
    expected_away_goals: Mapped[float] = mapped_column(Float)
    confidence: Mapped[Confidence] = mapped_column(Enum(Confidence))
    predicted_result: Mapped[Outcome] = mapped_column(Enum(Outcome))

    actual_result: Mapped[Outcome | None] = mapped_column(Enum(Outcome), nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    brier_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    log_loss: Mapped[float | None] = mapped_column(Float, nullable=True)

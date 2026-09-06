from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class ModelMetrics(Base):
    """A snapshot of a model's backtested performance over a period,
    optionally scoped to one competition (``competition_id`` set) or global
    (left null). Recomputed by the nightly job / on demand via
    /backtesting.
    """

    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(64), index=True)
    model_version: Mapped[str] = mapped_column(String(32))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)

    period_start: Mapped[datetime.datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime.datetime] = mapped_column(DateTime)
    matches_count: Mapped[int] = mapped_column(Integer)

    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    brier_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    log_loss: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class FeatureSnapshot(Base):
    """Caches the pre-match feature vector for a match so it isn't
    recomputed on every request (see README §Performance). Purely a
    performance cache: nothing here is a source of truth, everything can be
    rebuilt from matches/elo_history.
    """

    __tablename__ = "feature_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True)
    features_json: Mapped[str] = mapped_column(Text)
    computed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

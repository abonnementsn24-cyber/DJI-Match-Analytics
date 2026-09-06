"""Aggregates the ``predictions`` table into backtest reports: per model,
optionally sliced by competition/country/continent/season/confidence
level. Never re-runs the replay — it only reads what
``prediction_service``/``replay_engine`` already computed and
``evaluation_service`` already scored, so it's cheap to call from the API.

Model selection is Brier-first (§9 of the brief: accuracy alone is
misleading), with accuracy reported alongside for context.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from sqlalchemy.orm import Session

from ..analytics.metrics import (
    calibration_curve,
    calibration_error,
    classification_report,
)
from ..models.competition import Competition
from ..models.enums import Continent
from ..models.match import Match
from ..models.prediction import Prediction


@dataclass
class BacktestFilters:
    competition_id: int | None = None
    country_id: int | None = None
    continent: Continent | None = None
    season_id: int | None = None
    model_name: str | None = None
    min_confidence: str | None = None


@dataclass
class ModelBacktestReport:
    model_name: str
    matches_evaluated: int
    accuracy: float | None
    brier_score: float | None
    log_loss: float | None
    calibration_error: float | None
    classification: dict | None
    calibration_curve: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "matches_evaluated": self.matches_evaluated,
            "accuracy": round(self.accuracy, 4) if self.accuracy is not None else None,
            "brier_score": round(self.brier_score, 4) if self.brier_score is not None else None,
            "log_loss": round(self.log_loss, 4) if self.log_loss is not None else None,
            "calibration_error": (
                round(self.calibration_error, 4) if self.calibration_error is not None else None
            ),
            "classification": self.classification,
            "calibration_curve": self.calibration_curve,
        }


def _query_evaluated_predictions(db: Session, filters: BacktestFilters):
    query = (
        db.query(Prediction, Match)
        .join(Match, Prediction.match_id == Match.id)
        .filter(Prediction.actual_result.isnot(None))
    )
    if filters.competition_id is not None:
        query = query.filter(Match.competition_id == filters.competition_id)
    if filters.season_id is not None:
        query = query.filter(Match.season_id == filters.season_id)
    if filters.model_name is not None:
        query = query.filter(Prediction.model_name == filters.model_name)
    if filters.min_confidence is not None:
        query = query.filter(Prediction.confidence == filters.min_confidence)
    if filters.country_id is not None or filters.continent is not None:
        query = query.join(Competition, Match.competition_id == Competition.id)
        if filters.country_id is not None:
            query = query.filter(Competition.country_id == filters.country_id)
        if filters.continent is not None:
            query = query.filter(Competition.continent == filters.continent)
    return query


def backtest_model(db: Session, model_name: str, filters: BacktestFilters | None = None) -> ModelBacktestReport:
    filters = replace(filters or BacktestFilters(), model_name=model_name)
    rows = _query_evaluated_predictions(db, filters).all()

    if not rows:
        return ModelBacktestReport(
            model_name=model_name,
            matches_evaluated=0,
            accuracy=None,
            brier_score=None,
            log_loss=None,
            calibration_error=None,
            classification=None,
            calibration_curve=[],
        )

    y_true = [p.actual_result.value for p, _m in rows]
    y_pred = [p.predicted_result.value for p, _m in rows]
    briers = [p.brier_score for p, _m in rows if p.brier_score is not None]
    log_losses = [p.log_loss for p, _m in rows if p.log_loss is not None]

    calibration_samples = [
        (max(p.home_win_probability, p.draw_probability, p.away_win_probability), p.correct)
        for p, _m in rows
    ]
    curve = calibration_curve(calibration_samples)
    ece = calibration_error(curve, len(calibration_samples))

    classification = classification_report(y_true, y_pred)

    return ModelBacktestReport(
        model_name=model_name,
        matches_evaluated=len(rows),
        accuracy=sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == p) / len(rows),
        brier_score=sum(briers) / len(briers) if briers else None,
        log_loss=sum(log_losses) / len(log_losses) if log_losses else None,
        calibration_error=ece,
        classification=classification.as_dict() if classification else None,
        calibration_curve=[p.as_dict() for p in curve],
    )


def monthly_breakdown(db: Session, model_name: str, filters: BacktestFilters | None = None) -> list[dict]:
    """Powers the Model Lab's "performance over time" charts: accuracy and
    Brier score bucketed by the calendar month of the match date."""
    filters = replace(filters or BacktestFilters(), model_name=model_name)
    rows = _query_evaluated_predictions(db, filters).order_by(Match.utc_date.asc()).all()

    buckets: dict[str, list] = {}
    for prediction, match in rows:
        key = match.utc_date.strftime("%Y-%m")
        buckets.setdefault(key, []).append(prediction)

    out = []
    for month in sorted(buckets):
        preds = buckets[month]
        correct = sum(1 for p in preds if p.correct)
        briers = [p.brier_score for p in preds if p.brier_score is not None]
        out.append(
            {
                "month": month,
                "matches": len(preds),
                "accuracy": round(correct / len(preds), 4) if preds else None,
                "brier_score": round(sum(briers) / len(briers), 4) if briers else None,
            }
        )
    return out


def backtest_compare(
    db: Session, models: list[str], filters: BacktestFilters | None = None
) -> dict:
    reports = {model: backtest_model(db, model, filters) for model in models}
    scored = {m: r.brier_score for m, r in reports.items() if r.brier_score is not None}
    best_model = min(scored, key=scored.get) if scored else None

    return {
        "best_model": best_model,
        "models": {model: report.as_dict() for model, report in reports.items()},
    }


def persist_metrics_snapshot(db: Session, models: list[str], model_version: str = "1.0.0") -> int:
    """Writes one ``model_metrics`` row per model (global — the full
    evaluated history to date), for the nightly job (§19) to track model
    performance over time without re-running a full backtest on every
    dashboard load.
    """
    from ..models.metrics import ModelMetrics
    from ..models.prediction import Prediction

    now = datetime.utcnow()
    written = 0

    for model in models:
        report = backtest_model(db, model)
        if report.matches_evaluated == 0:
            continue

        earliest = (
            db.query(Prediction.generated_at)
            .filter(Prediction.model_name == model, Prediction.actual_result.isnot(None))
            .order_by(Prediction.generated_at.asc())
            .first()
        )
        period_start = earliest[0] if earliest else now

        db.add(
            ModelMetrics(
                model_name=model,
                model_version=model_version,
                competition_id=None,
                period_start=period_start,
                period_end=now,
                matches_count=report.matches_evaluated,
                accuracy=report.accuracy,
                brier_score=report.brier_score,
                log_loss=report.log_loss,
            )
        )
        written += 1

    db.commit()
    return written

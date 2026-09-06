"""Trains Model 5 (ML) on stored match history.

Chronological split only — never a random train/test split on temporal
data (§7 of the brief): the first ~70% of matches by date train the
model, the next ~15% validate it, and the most recent ~15% test it. Below
``MIN_TRAINING_SAMPLES`` we refuse to train at all rather than fit a
model on a handful of matches and pretend it's meaningful.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session

from ..analytics.metrics import brier_score, log_loss_single
from ..analytics.replay_engine import iter_matches_chronologically
from ..core.config import get_settings
from ..core.logging import get_logger
from .artifact import MODEL_VERSION, save_artifact
from .features import FEATURE_NAMES, build_feature_vector

logger = get_logger(__name__)

MIN_TRAINING_SAMPLES = 60
ALGORITHMS = {
    "logistic_regression": lambda: LogisticRegression(max_iter=1000),
    "hist_gradient_boosting": lambda: HistGradientBoostingClassifier(random_state=42),
}


@dataclass
class Sample:
    features: list[float]
    label: str
    date: datetime.datetime


def _collect_samples(db: Session) -> list[Sample]:
    settings = get_settings()
    samples: list[Sample] = []

    for step in iter_matches_chronologically(db):
        match = step.match
        if not match.is_finished:
            continue

        home_played = step.state.matches_played(match.home_team_id)
        away_played = step.state.matches_played(match.away_team_id)
        if home_played < settings.min_matches_for_prediction or away_played < settings.min_matches_for_prediction:
            continue

        features = build_feature_vector(step.state, step.elo, step.ctx, match.utc_date)
        if match.home_goals > match.away_goals:
            label = "HOME"
        elif match.home_goals < match.away_goals:
            label = "AWAY"
        else:
            label = "DRAW"

        samples.append(Sample(features=features, label=label, date=match.utc_date))

    return samples


def _chronological_split(samples: list[Sample]) -> tuple[list[Sample], list[Sample], list[Sample]]:
    n = len(samples)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    return samples[:train_end], samples[train_end:val_end], samples[val_end:]


def _evaluate(model, samples: list[Sample]) -> dict:
    if not samples:
        return {"matches": 0, "accuracy": None, "brier_score": None, "log_loss": None}

    x = [s.features for s in samples]
    y_true = [s.label for s in samples]
    proba = model.predict_proba(x)
    classes = list(model.classes_)

    def ordered_proba(row):
        return tuple(row[classes.index(c)] if c in classes else 0.0 for c in ("HOME", "DRAW", "AWAY"))

    predictions = model.predict(x)
    correct = sum(1 for p, t in zip(predictions, y_true, strict=True) if p == t)
    briers = [brier_score(ordered_proba(row), truth) for row, truth in zip(proba, y_true, strict=True)]
    log_losses = [log_loss_single(ordered_proba(row), truth) for row, truth in zip(proba, y_true, strict=True)]

    return {
        "matches": len(samples),
        "accuracy": correct / len(samples),
        "brier_score": sum(briers) / len(briers),
        "log_loss": sum(log_losses) / len(log_losses),
    }


def train_model(db: Session, algorithm: str = "hist_gradient_boosting") -> dict:
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Algorithme inconnu: {algorithm!r} (attendu: {list(ALGORITHMS)})")

    samples = _collect_samples(db)
    if len(samples) < MIN_TRAINING_SAMPLES:
        return {
            "trained": False,
            "reason": (
                f"Seulement {len(samples)} matchs exploitables (minimum requis: "
                f"{MIN_TRAINING_SAMPLES}). Synchronisez plus d'historique avant d'entraîner le modèle ML."
            ),
        }

    train, val, test = _chronological_split(samples)
    if not train or not test:
        return {"trained": False, "reason": "Split chronologique impossible (pas assez de matchs)."}

    model = ALGORITHMS[algorithm]()
    model.fit([s.features for s in train], [s.label for s in train])

    val_report = _evaluate(model, val)
    test_report = _evaluate(model, test)

    save_artifact(
        {
            "model": model,
            "algorithm": algorithm,
            "feature_names": FEATURE_NAMES,
            "version": MODEL_VERSION,
            "trained_at": datetime.datetime.utcnow().isoformat(),
            "train_samples": len(train),
            "val_samples": len(val),
            "test_samples": len(test),
            "val_report": val_report,
            "test_report": test_report,
        }
    )

    logger.info(
        "Modèle ML entraîné (%s): %d train / %d val / %d test — accuracy test=%.3f",
        algorithm,
        len(train),
        len(val),
        len(test),
        test_report["accuracy"] or 0.0,
    )

    return {
        "trained": True,
        "algorithm": algorithm,
        "train_samples": len(train),
        "val_samples": len(val),
        "test_samples": len(test),
        "val_report": val_report,
        "test_report": test_report,
    }

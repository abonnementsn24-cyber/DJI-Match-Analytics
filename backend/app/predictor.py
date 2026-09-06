"""Ties the prediction models together into one result, including the
confidence index and the "insufficient data" fallback.
"""
from __future__ import annotations

from dataclasses import dataclass

from .elo import EloRatings
from .poisson_model import MatchProbabilities
from .team_stats import TeamStats
from .variants import MODEL_NAMES, predict_with_model

MIN_MATCHES_FOR_PREDICTION = 5
LOW_CONFIDENCE_THRESHOLD = 10
MEDIUM_CONFIDENCE_THRESHOLD = 25

DEFAULT_MODEL = "combined"


@dataclass
class PredictionResult:
    home_team: str
    away_team: str
    model: str
    reliable: bool
    confidence: str | None
    reason: str | None
    probabilities: MatchProbabilities | None

    def as_dict(self) -> dict:
        base = {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "model": self.model,
            "reliable": self.reliable,
        }
        if not self.reliable:
            base["reason"] = self.reason
            return base
        base["confidence"] = self.confidence
        base.update(self.probabilities.as_dict())
        return base


def _confidence_level(home_played: int, away_played: int) -> str:
    sample = min(home_played, away_played)
    if sample < LOW_CONFIDENCE_THRESHOLD:
        return "faible"
    if sample < MEDIUM_CONFIDENCE_THRESHOLD:
        return "moyenne"
    return "elevee"


def predict(
    ratings: EloRatings,
    stats: TeamStats,
    home_team: str,
    away_team: str,
    model: str = DEFAULT_MODEL,
) -> PredictionResult:
    if model not in MODEL_NAMES:
        raise ValueError(f"Modèle inconnu: {model!r} (attendu: {MODEL_NAMES})")

    home_played = stats.matches_played(home_team)
    away_played = stats.matches_played(away_team)

    if home_played < MIN_MATCHES_FOR_PREDICTION or away_played < MIN_MATCHES_FOR_PREDICTION:
        return PredictionResult(
            home_team=home_team,
            away_team=away_team,
            model=model,
            reliable=False,
            confidence=None,
            reason=(
                "Données insuffisantes : au moins "
                f"{MIN_MATCHES_FOR_PREDICTION} matchs par équipe sont nécessaires "
                "pour produire une prédiction fiable."
            ),
            probabilities=None,
        )

    probabilities = predict_with_model(model, ratings, stats, home_team, away_team)
    confidence = _confidence_level(home_played, away_played)

    return PredictionResult(
        home_team=home_team,
        away_team=away_team,
        model=model,
        reliable=True,
        confidence=confidence,
        reason=None,
        probabilities=probabilities,
    )

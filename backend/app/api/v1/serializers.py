"""Shared row -> JSON-dict conversions for the v1 API. Top-5 scorelines are
never stored (see docs/DATA_PIPELINE.md) — they're recomputed on the fly
from the stored expected goals via the Poisson matrix.
"""
from __future__ import annotations

from ...analytics.poisson import predict_match
from ...models.competition import Competition
from ...models.match import Match
from ...models.prediction import Prediction
from ...models.team import Team


def serialize_team(team: Team | None) -> dict | None:
    if team is None:
        return None
    return {
        "id": team.id,
        "name": team.canonical_name,
        "short_name": team.short_name,
        "code": team.code,
        "logo": team.logo,
        "team_type": team.team_type.value,
    }


def serialize_competition(competition: Competition | None) -> dict | None:
    if competition is None:
        return None
    return {
        "id": competition.id,
        "name": competition.canonical_name,
        "code": competition.code,
        "country": competition.country.name if competition.country else None,
        "continent": competition.continent.value,
        "type": competition.competition_type.value,
        "data_quality": competition.data_quality.value,
        "logo": competition.logo,
    }


def serialize_prediction(prediction: Prediction, top_n: int = 5) -> dict:
    probs = predict_match(
        prediction.expected_home_goals, prediction.expected_away_goals, top_n=top_n
    )
    return {
        "model_name": prediction.model_name,
        "model_version": prediction.model_version,
        "generated_at": prediction.generated_at.isoformat(),
        "locked": prediction.locked,
        "home_win_probability": round(prediction.home_win_probability, 4),
        "draw_probability": round(prediction.draw_probability, 4),
        "away_win_probability": round(prediction.away_win_probability, 4),
        "expected_home_goals": round(prediction.expected_home_goals, 2),
        "expected_away_goals": round(prediction.expected_away_goals, 2),
        "btts_probability": probs.as_dict()["btts_probability"],
        "over_2_5_probability": probs.as_dict()["over_2_5_probability"],
        "top_scores": probs.as_dict()["top_scores"],
        "confidence": prediction.confidence.value,
        "predicted_result": prediction.predicted_result.value,
        "actual_result": prediction.actual_result.value if prediction.actual_result else None,
        "correct": prediction.correct,
        "brier_score": round(prediction.brier_score, 4) if prediction.brier_score is not None else None,
        "log_loss": round(prediction.log_loss, 4) if prediction.log_loss is not None else None,
    }


def serialize_match_summary(match: Match) -> dict:
    return {
        "id": match.id,
        "utc_date": match.utc_date.isoformat(),
        "status": match.status.value,
        "matchday": match.matchday,
        "competition": serialize_competition(match.competition),
        "home_team": serialize_team(match.home_team),
        "away_team": serialize_team(match.away_team),
        "home_goals": match.home_goals,
        "away_goals": match.away_goals,
        "winner": match.winner.value if match.winner else None,
    }

"""Loads the trained ML classifier (if any) and adapts it to the same
``(state, elo, ctx, as_of) -> (home_p, draw_p, away_p, exp_home, exp_away)``
contract the other model variants use, so the replay engine and the API
can treat all five models uniformly.

The classifier only ever predicts the 1/N/2 outcome — it has no notion of
goals. Expected goals (for display, and to build the top-5 scoreline list)
still come from the Poisson+Elo+form ensemble; this is a deliberate hybrid,
documented in docs/MODELS.md, not a claim that the scorelines themselves
are ML-generated.
"""
from __future__ import annotations

from collections.abc import Callable

from ..analytics.model_variants import MatchContext, expected_goals_ensemble
from .artifact import load_artifact
from .features import build_feature_vector

PredictFn = Callable[..., tuple[float, float, float, float, float] | None]


def load_latest_model() -> dict | None:
    return load_artifact()


def make_predict_fn(artifact: dict) -> PredictFn:
    model = artifact["model"]
    classes = list(model.classes_)

    def predict_fn(state, elo, ctx: MatchContext, as_of):
        features = build_feature_vector(state, elo, ctx, as_of)
        proba = model.predict_proba([features])[0]

        def p(label: str) -> float:
            return float(proba[classes.index(label)]) if label in classes else 0.0

        home_p, draw_p, away_p = p("HOME"), p("DRAW"), p("AWAY")
        total = home_p + draw_p + away_p
        if total <= 0:
            return None
        home_p, draw_p, away_p = home_p / total, draw_p / total, away_p / total

        lam_home, lam_away = expected_goals_ensemble(state, elo, ctx, as_of)
        return home_p, draw_p, away_p, lam_home, lam_away

    return predict_fn


def predict_with_ml_model(state, elo, ctx: MatchContext, as_of):
    """Convenience one-shot call (loads the artifact each time — fine for
    the API's single-match /predict endpoint; the replay engine uses
    ``make_predict_fn`` once per run instead to avoid reloading per match)."""
    artifact = load_latest_model()
    if artifact is None:
        return None
    return make_predict_fn(artifact)(state, elo, ctx, as_of)

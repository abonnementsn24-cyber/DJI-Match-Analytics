"""Importing this package registers every ORM model on ``Base.metadata`` —
required before ``create_all()`` or Alembic autogenerate."""
from .competition import Competition, Season
from .country import Country
from .elo import EloHistory
from .enums import (
    CompetitionType,
    Confidence,
    Continent,
    DataQuality,
    MatchStatus,
    MatchWinner,
    Outcome,
    TeamType,
)
from .mapping import ProviderCompetitionMapping, ProviderTeamMapping
from .match import Match
from .metrics import FeatureSnapshot, ModelMetrics
from .prediction import Prediction
from .stats import TeamMatchStats
from .team import CompetitionSeasonTeam, Team

__all__ = [
    "Competition",
    "CompetitionSeasonTeam",
    "CompetitionType",
    "Confidence",
    "Continent",
    "Country",
    "DataQuality",
    "EloHistory",
    "FeatureSnapshot",
    "Match",
    "MatchStatus",
    "MatchWinner",
    "ModelMetrics",
    "Outcome",
    "Prediction",
    "ProviderCompetitionMapping",
    "ProviderTeamMapping",
    "Season",
    "Team",
    "TeamMatchStats",
    "TeamType",
]

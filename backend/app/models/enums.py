from __future__ import annotations

import enum


class Continent(str, enum.Enum):
    AFRICA = "AFRICA"
    EUROPE = "EUROPE"
    SOUTH_AMERICA = "SOUTH_AMERICA"
    NORTH_AMERICA = "NORTH_AMERICA"
    ASIA = "ASIA"
    OCEANIA = "OCEANIA"
    INTERNATIONAL = "INTERNATIONAL"


class CompetitionType(str, enum.Enum):
    LEAGUE = "LEAGUE"
    CUP = "CUP"
    SUPER_CUP = "SUPER_CUP"
    PLAYOFF = "PLAYOFF"
    QUALIFICATION = "QUALIFICATION"
    INTERNATIONAL = "INTERNATIONAL"


class DataQuality(str, enum.Enum):
    A = "A"  # Rich history + results + standings + enough stats
    B = "B"  # Decent history, some stats missing
    C = "C"  # Sparse data
    D = "D"  # Insufficient for a reliable estimate


class TeamType(str, enum.Enum):
    CLUB = "CLUB"
    NATIONAL_TEAM = "NATIONAL_TEAM"


class MatchStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    TIMED = "TIMED"
    LIVE = "LIVE"
    IN_PLAY = "IN_PLAY"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    POSTPONED = "POSTPONED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class MatchWinner(str, enum.Enum):
    HOME_TEAM = "HOME_TEAM"
    AWAY_TEAM = "AWAY_TEAM"
    DRAW = "DRAW"


class Outcome(str, enum.Enum):
    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


class Confidence(str, enum.Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


FINISHED_STATUSES = {MatchStatus.FINISHED}
LIVE_STATUSES = {MatchStatus.LIVE, MatchStatus.IN_PLAY, MatchStatus.PAUSED}
UPCOMING_STATUSES = {MatchStatus.SCHEDULED, MatchStatus.TIMED}

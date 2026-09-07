"""A curated priority list for *automatic* synchronization — not a coverage
restriction. Discovery (``discovery_service.py``) still finds every
competition the provider exposes with no static list at all; this module
only decides which of the already-discovered competitions the scheduler
proactively keeps in sync, mirroring the "PredictionQueue" priority concept
from the brief (§13 of the extension): sync the popular leagues users
actually ask about first, then let anything else be synced on demand via
``POST /api/v1/admin/sync``.

Codes are football-data.org competition codes, verified live against
``GET /v4/competitions`` (189 competitions, 62 areas). **Saudi Arabia is not
among them** — football-data.org does not expose the Saudi Pro League on
any plan. Supporting it would mean adding a second ``FootballProvider``
(API-Football, SportMonks, ...) that does cover it; the ``providers/``
abstraction is built for exactly that, but no such provider is wired up
without real credentials for one.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PopularLeague:
    code: str
    label: str
    country: str


POPULAR_LEAGUES: tuple[PopularLeague, ...] = (
    PopularLeague("PL", "Premier League", "Angleterre"),
    PopularLeague("PD", "La Liga (Primera División)", "Espagne"),
    PopularLeague("SA", "Serie A", "Italie"),
    PopularLeague("BL1", "Bundesliga", "Allemagne"),
    PopularLeague("FL1", "Ligue 1", "France"),
    PopularLeague("DED", "Eredivisie", "Pays-Bas"),
    PopularLeague("PPL", "Primeira Liga", "Portugal"),
    PopularLeague("BSA", "Campeonato Brasileiro Série A", "Brésil"),
    PopularLeague("ELC", "Championship", "Angleterre"),
    PopularLeague("CL", "UEFA Champions League", "Europe"),
)

# Known gaps: leagues frequently requested that this provider does not
# expose at all (kept here, rather than silently dropped, so the reason
# shows up wherever this list is surfaced).
UNAVAILABLE_FROM_PROVIDER: tuple[dict, ...] = (
    {
        "requested": "Arabie Saoudite — Saudi Pro League",
        "reason": "Non exposée par football-data.org (aucune compétition sous 'Saudi Arabia' dans les 189 disponibles).",
    },
)


def popular_league_codes() -> list[str]:
    return [league.code for league in POPULAR_LEAGUES]

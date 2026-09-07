"""Discovers which competitions a provider currently exposes and reconciles
that list with our database — no static list of leagues anywhere. Running
this periodically (see app/jobs) is how a brand-new competition shows up
in EMDJI without a code change or deployment.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..models.competition import Competition
from ..models.mapping import ProviderCompetitionMapping
from ..providers.base import FootballProvider
from .normalization_service import get_or_create_competition

logger = get_logger(__name__)


@dataclass
class DiscoveryReport:
    provider: str
    total_seen: int
    newly_added: int
    updated: int

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "total_seen": self.total_seen,
            "newly_added": self.newly_added,
            "updated": self.updated,
        }


def discover_competitions(db: Session, provider: FootballProvider) -> DiscoveryReport:
    existing_provider_ids = {
        row.provider_competition_id
        for row in db.query(ProviderCompetitionMapping.provider_competition_id).filter(
            ProviderCompetitionMapping.provider == provider.name
        )
    }

    competitions = provider.get_competitions()
    added = 0
    updated = 0

    for competition in competitions:
        is_new = competition.provider_id not in existing_provider_ids
        get_or_create_competition(db, provider.name, competition)
        if is_new:
            added += 1
        else:
            updated += 1

    db.commit()
    logger.info(
        "Discovery (%s): %d compétitions vues, %d nouvelles, %d mises à jour",
        provider.name,
        len(competitions),
        added,
        updated,
    )
    return DiscoveryReport(
        provider=provider.name, total_seen=len(competitions), newly_added=added, updated=updated
    )


def list_world_tree(db: Session) -> list[dict]:
    """Continent → country → competitions, built entirely from what's in
    our database (itself populated only by ``discover_competitions``)."""
    competitions = db.query(Competition).filter(Competition.active.is_(True)).all()

    tree: dict[str, dict[tuple[int | None, str], list[dict]]] = {}
    for comp in competitions:
        continent = comp.continent.value
        country_key = (comp.country.id, comp.country.name) if comp.country else (None, "International")
        tree.setdefault(continent, {}).setdefault(country_key, []).append(
            {
                "id": comp.id,
                "name": comp.canonical_name,
                "code": comp.code,
                "type": comp.competition_type.value,
                "data_quality": comp.data_quality.value,
                "logo": comp.logo,
            }
        )

    return [
        {
            "continent": continent,
            "countries": [
                {"country_id": country_id, "country": country_name, "competitions": comps}
                for (country_id, country_name), comps in sorted(countries.items(), key=lambda kv: kv[0][1])
            ],
        }
        for continent, countries in sorted(tree.items())
    ]

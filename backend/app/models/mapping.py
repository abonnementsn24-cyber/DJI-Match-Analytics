"""Provider → canonical entity mappings.

The same club or competition can be named differently across data
providers ("Manchester United" vs "Man United" vs "Manchester Utd"). We
never auto-merge on name similarity alone: a mapping row is created
deliberately by the normalization service, keyed on the provider's own
stable ID, which is unambiguous.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class ProviderTeamMapping(Base):
    __tablename__ = "provider_team_mappings"
    __table_args__ = (UniqueConstraint("provider", "provider_team_id", name="uq_provider_team"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    provider_team_id: Mapped[str] = mapped_column(String(64))
    provider_name: Mapped[str] = mapped_column(String(255))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))


class ProviderCompetitionMapping(Base):
    __tablename__ = "provider_competition_mappings"
    __table_args__ = (
        UniqueConstraint("provider", "provider_competition_id", name="uq_provider_competition"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    provider_competition_id: Mapped[str] = mapped_column(String(64))
    provider_name: Mapped[str] = mapped_column(String(255))
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))

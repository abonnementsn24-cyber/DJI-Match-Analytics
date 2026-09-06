"""Factory for provider instances, keyed by name. Adding provider #2 means
registering it here — nothing else in the codebase needs to change."""
from __future__ import annotations

from .base import FootballProvider
from .football_data import FootballDataProvider

_PROVIDERS: dict[str, type[FootballProvider]] = {
    FootballDataProvider.name: FootballDataProvider,
}


def get_provider(name: str = FootballDataProvider.name) -> FootballProvider:
    try:
        provider_cls = _PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(f"Fournisseur inconnu: {name!r} (disponibles: {list(_PROVIDERS)})") from exc
    return provider_cls()


def register_provider(name: str, provider_cls: type[FootballProvider]) -> None:
    _PROVIDERS[name] = provider_cls

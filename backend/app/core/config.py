"""Central application settings, loaded from environment variables.

Nothing here is a hardcoded secret: every credential comes from the
environment (see ``.env.example`` at the repo root). ``demo_mode`` is
derived, not set directly — the app runs in demo mode whenever no real
football-data.org API key is configured, and switches to real data the
moment one is.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "sqlite:///./match_analytics.db"

    # football-data.org
    football_data_api_key: str | None = None
    football_data_base_url: str = "https://api.football-data.org/v4"

    # Admin / sync endpoints
    admin_api_token: str | None = None

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # Feature engineering
    form_window_short: int = 5
    form_window_long: int = 10
    h2h_max_matches: int = 5
    min_matches_for_prediction: int = 5

    # Elo
    elo_initial_rating: float = 1500.0
    elo_home_advantage: float = 65.0
    elo_k_factor: float = 20.0

    # Ensemble weights (must sum to 1.0). Equal weighting is a deliberate
    # placeholder — tune it from real /backtesting comparisons, not by hand.
    ensemble_weight_basic: float = 1 / 3
    ensemble_weight_form: float = 1 / 3
    ensemble_weight_elo: float = 1 / 3
    ensemble_h2h_max_adjustment: float = 0.15
    ensemble_rest_max_adjustment: float = 0.05

    # Automatic updates (§19 of the brief). Disabled in tests (see
    # tests/conftest.py) so pytest never starts a background scheduler.
    enable_scheduler: bool = True
    discover_interval_hours: int = 24
    sync_popular_leagues_interval_hours: int = 6
    evaluate_interval_minutes: int = 30
    metrics_snapshot_interval_hours: int = 24

    @property
    def demo_mode(self) -> bool:
        return not bool(self.football_data_api_key)

    @property
    def is_admin_protected(self) -> bool:
        return bool(self.admin_api_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()

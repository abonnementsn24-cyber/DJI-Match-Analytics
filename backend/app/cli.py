"""Command-line entry point for admin operations.

Usage:
    python -m app.cli discover
    python -m app.cli sync PL 2025
    python -m app.cli generate-predictions PL
    python -m app.cli evaluate
"""
from __future__ import annotations

import argparse
import sys

from .core.logging import configure_logging, get_logger
from .db.session import SessionLocal, init_db
from .providers.registry import get_provider
from .services.discovery_service import discover_competitions
from .services.sync_service import sync_competition

logger = get_logger(__name__)


def cmd_discover(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        provider = get_provider(args.provider)
        report = discover_competitions(db, provider)
        print(report.as_dict())
        return 0
    finally:
        db.close()


def cmd_sync(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        provider = get_provider(args.provider)
        report = sync_competition(db, provider, args.code, season_year=args.season)
        print(report.as_dict())
        return 1 if report.errors else 0
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


def cmd_generate_predictions(args: argparse.Namespace) -> int:
    from .services.prediction_service import generate_predictions_for_competition

    db = SessionLocal()
    try:
        from .services.sync_service import get_competition_by_code

        provider = get_provider(args.provider)
        competition = get_competition_by_code(db, provider.name, args.code)
        if competition is None:
            print(f"Compétition inconnue: {args.code}", file=sys.stderr)
            return 1
        result = generate_predictions_for_competition(db, competition.id)
        print(result)
        return 0
    finally:
        db.close()


def cmd_evaluate(args: argparse.Namespace) -> int:
    from .services.evaluation_service import evaluate_finished_predictions

    db = SessionLocal()
    try:
        count = evaluate_finished_predictions(db)
        print(f"{count} prédictions évaluées.")
        return 0
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("--provider", default="football-data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Découvre les compétitions disponibles")
    discover_parser.set_defaults(func=cmd_discover)

    sync_parser = subparsers.add_parser("sync", help="Synchronise une compétition")
    sync_parser.add_argument("code", help="Code de la compétition, ex: PL")
    sync_parser.add_argument("season", type=int, nargs="?", default=None, help="Année de saison, ex: 2025")
    sync_parser.set_defaults(func=cmd_sync)

    predict_parser = subparsers.add_parser(
        "generate-predictions", help="Génère les prédictions manquantes pour une compétition"
    )
    predict_parser.add_argument("code")
    predict_parser.set_defaults(func=cmd_generate_predictions)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Évalue les prédictions des matchs désormais terminés"
    )
    evaluate_parser.set_defaults(func=cmd_evaluate)

    return parser


def main() -> int:
    configure_logging()
    init_db()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

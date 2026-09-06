from fastapi import APIRouter

from . import admin, backtesting, competitions, matches, models, system, teams

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(matches.router)
api_router.include_router(teams.router)
api_router.include_router(competitions.router)
api_router.include_router(models.router)
api_router.include_router(backtesting.router)
api_router.include_router(admin.router)
api_router.include_router(system.router)

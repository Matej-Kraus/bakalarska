from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.club import router as club_router
from app.api.routes.events import router as events_router
from app.api.routes.export import router as export_router
from app.api.routes.lineup import router as lineup_router
from app.api.routes.matches import router as matches_router
from app.api.routes.players import router as players_router
from app.api.routes.ratings import router as ratings_router
from app.api.routes.reports import router as reports_router
from app.api.routes.seasons import router as seasons_router
from app.api.routes.stats import router as stats_router
from app.api.routes.substitutions import router as substitutions_router

api_router = APIRouter()
api_router.include_router(seasons_router)
api_router.include_router(matches_router)
api_router.include_router(auth_router)
api_router.include_router(club_router)
api_router.include_router(events_router)
api_router.include_router(lineup_router)
api_router.include_router(stats_router)
api_router.include_router(reports_router)
api_router.include_router(export_router)
api_router.include_router(ratings_router)
api_router.include_router(analytics_router)
api_router.include_router(substitutions_router)
api_router.include_router(players_router)

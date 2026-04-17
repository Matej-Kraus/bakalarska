from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.club import router as club_router
from app.exceptions import AppError
from app.api.routes.events import router as events_router
from app.api.routes.export import router as export_router
from app.api.routes.ratings import router as ratings_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.substitutions import router as substitutions_router
from app.api.routes.players import router as players_router
from app.api.routes.seasons import router as seasons_router
from app.api.routes.matches import router as matches_router
from app.api.routes.lineup import router as lineup_router
from app.api.routes.stats import router as stats_router
from app.api.routes.reports import router as reports_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings

app = FastAPI(title="Trainer App API", version="0.1.0")


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_base_url.rstrip("/"),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(seasons_router)
app.include_router(matches_router)
app.include_router(auth_router)
app.include_router(club_router)
app.include_router(events_router)
app.include_router(lineup_router)
app.include_router(stats_router)
app.include_router(reports_router)
app.include_router(export_router)
app.include_router(ratings_router)
app.include_router(analytics_router)
app.include_router(substitutions_router)
@app.get("/")
def root():
    return {"message": "Trainer App API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(players_router)
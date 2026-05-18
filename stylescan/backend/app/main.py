"""
VISAI API — Entry point

Start with: uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import init_db
# Import all models so Base.metadata registers them before init_db runs
from app.models import (  # noqa: F401
    analysis as _m_analysis,
    barber as _m_barber,
    consent as _m_consent,
    barber_reference_photos as _m_ref_photos,
    barber_leaderboard_stats as _m_leaderboard,
    parental_consent_requests as _m_parental,
    barber_telegram_accounts as _m_telegram,
)
from app.api.routes import admin, analysis, barbers, payments, visuals, references, barber_gamification

# Barber reference images directory (populated by barber_instagram_agent --save-images)
_BARBER_REFS_DIR = Path(__file__).parent.parent / "knowledge_base" / "barber_references" / "images"
_BARBER_REFS_DIR.mkdir(parents=True, exist_ok=True)

# Mannequin illustration library (created by Lucas, flat-design per cranial type + cut)
_ILLUSTRATIONS_DIR = Path(__file__).parent.parent / "knowledge_base" / "haircut_illustrations"
_ILLUSTRATIONS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Global rate limiter (keyed by IP)
limiter = Limiter(key_func=get_remote_address)


async def _purge_expired_analyses():
    """Delete analysis rows past their retention window."""
    from sqlalchemy import delete
    from app.core.database import AsyncSessionLocal
    from app.models.analysis import Analysis

    async with AsyncSessionLocal() as db:
        cutoff = datetime.now(timezone.utc)
        result = await db.execute(
            delete(Analysis).where(Analysis.expires_at < cutoff)
        )
        await db.commit()
        if result.rowcount:
            logger.info("Data retention: purged %d expired analyses", result.rowcount)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VISAI API starting — initializing database")
    await init_db()
    logger.info("Database ready")

    # Wire APScheduler for background jobs
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.jobs import (
        recalculate_leaderboard_rankings,
        send_weekly_telegram_summary,
        auto_approve_high_quality_photos,
    )

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Daily jobs at 03:00 UTC
    scheduler.add_job(_purge_expired_analyses, "cron", hour=3, minute=0, id="purge_analyses")
    scheduler.add_job(recalculate_leaderboard_rankings, "cron", hour=3, minute=0, id="leaderboard_rankings")
    scheduler.add_job(auto_approve_high_quality_photos, "cron", hour=3, minute=0, id="approve_photos")

    # Weekly job: Sunday 08:00 UTC
    scheduler.add_job(send_weekly_telegram_summary, "cron", day_of_week=6, hour=8, minute=0, id="telegram_summary")

    scheduler.start()
    logger.info("APScheduler started with 4 background jobs")
    logger.info("  - Daily (03:00 UTC): Data retention purge, leaderboard recalc, photo auto-approval")
    logger.info("  - Weekly (Sunday 08:00 UTC): Telegram weekly summary")

    yield

    scheduler.shutdown(wait=False)
    logger.info("VISAI API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_ALLOWED_ORIGINS = [
    "https://visaiapp.com",
    "https://www.visaiapp.com",
    "https://visai.es",
    "https://www.visai.es",
]

_DEBUG_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEBUG_ORIGINS if settings.DEBUG else _ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(analysis.router, prefix="/api/v1")
app.include_router(barbers.router, prefix="/api/v1")
app.include_router(barber_gamification.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(visuals.router, prefix="/api/v1")
app.include_router(references.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

# Serve barber reference images (populated by barber_instagram_agent --save-images)
app.mount("/barber-refs", StaticFiles(directory=str(_BARBER_REFS_DIR)), name="barber-refs")

# Serve mannequin illustration library (flat-design per cranial type + cut)
app.mount("/illustrations", StaticFiles(directory=str(_ILLUSTRATIONS_DIR)), name="illustrations")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}

"""
VISAI API — Entry point

Start with: uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
# Import all models so Base.metadata registers them before init_db runs
from app.models import analysis as _m_analysis, barber as _m_barber, consent as _m_consent  # noqa: F401
from app.api.routes import admin, analysis, barbers, payments, visuals

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VISAI API starting — initializing database")
    await init_db()
    logger.info("Database ready")
    yield
    logger.info("StyleScan API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://visai.es", "https://www.visai.es"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1")
app.include_router(barbers.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(visuals.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}

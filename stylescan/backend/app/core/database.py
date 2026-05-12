from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Ensure the DB parent directory exists (Railway volume is mounted after image build)
if settings.DATABASE_URL.startswith("sqlite"):
    _raw = settings.DATABASE_URL.split("///", 1)[-1]          # e.g. "./knowledge_base/stylescan.db"
    Path(_raw.replace("./", "", 1)).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_analyses_columns)


def _migrate_analyses_columns(connection):
    """Add columns introduced after initial schema without Alembic."""
    existing = {row[1] for row in connection.execute(text("PRAGMA table_info(analyses)"))}
    additions = [
        ("user_email",           "VARCHAR(255)"),
        ("marketing_consent",    "BOOLEAN NOT NULL DEFAULT 0"),
        ("marketing_consent_at", "DATETIME"),
    ]
    for col, col_type in additions:
        if col not in existing:
            connection.execute(text(f"ALTER TABLE analyses ADD COLUMN {col} {col_type}"))

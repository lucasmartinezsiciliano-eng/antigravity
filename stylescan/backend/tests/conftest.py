"""
Test configuration and fixtures for VISAI API tests.
"""

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.core.database import Base, get_db
from app.main import app


# Shared in-memory SQLite — StaticPool ensures all sessions use the same connection
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create test database and tables using a shared in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    yield session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """FastAPI test client with get_db overridden to use in-memory test database."""

    async def override_get_db():
        async with test_db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_barber(test_db):
    """Create a sample barber for tests."""
    from app.models.barber import BarberPartner

    async with test_db() as db:
        barber = BarberPartner(
            id="test-barber-001",
            name="Juan García",
            barbershop_name="Barbería García",
            email="juan@example.com",
            phone="+34666666666",
            city="Barcelona",
            province="Barcelona",
            promo_code="JUAN123",
        )
        db.add(barber)
        await db.commit()
        await db.refresh(barber)
        return barber


@pytest_asyncio.fixture
async def sample_leaderboard_stats(test_db, sample_barber):
    """Create sample leaderboard stats."""
    from app.models.barber_leaderboard_stats import BarberLeaderboardStats, RankingTier

    async with test_db() as db:
        stats = BarberLeaderboardStats(
            id="stats-001",
            barber_partner_id=sample_barber.id,
            clients_this_week=10,
            clients_this_month=45,
            clients_all_time=200,
            current_tier=RankingTier.GOLD,
        )
        db.add(stats)
        await db.commit()
        await db.refresh(stats)
        return stats


@pytest_asyncio.fixture
async def sample_telegram_account(test_db, sample_barber):
    """Create sample Telegram account."""
    from app.models.barber_telegram_accounts import BarberTelegramAccount

    async with test_db() as db:
        account = BarberTelegramAccount(
            id="tg-001",
            barber_partner_id=sample_barber.id,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
            telegram_username="juangarcia",
            first_name="Juan",
            is_connected=True,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

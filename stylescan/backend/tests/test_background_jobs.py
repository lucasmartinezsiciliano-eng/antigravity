"""
Tests for background jobs.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import select

import app.jobs.background_jobs as bg_jobs
from app.jobs import (
    recalculate_leaderboard_rankings,
    auto_approve_high_quality_photos,
)
from app.models.barber_leaderboard_stats import BarberLeaderboardStats, RankingTier
from app.models.barber_reference_photos import BarberReferencePhoto, PhotoValidationStatus


@pytest.mark.asyncio
async def test_recalculate_leaderboard_rankings(sample_leaderboard_stats, test_db):
    """Test leaderboard ranking recalculation job."""
    bg_jobs.AsyncSessionLocal = test_db
    try:
        await recalculate_leaderboard_rankings()
    finally:
        from app.core.database import AsyncSessionLocal
        bg_jobs.AsyncSessionLocal = AsyncSessionLocal

    async with test_db() as db:
        result = await db.execute(
            select(BarberLeaderboardStats).where(
                BarberLeaderboardStats.id == sample_leaderboard_stats.id
            )
        )
        updated_stats = result.scalar_one()

        assert updated_stats.week_ranking_position is not None
        assert updated_stats.month_ranking_position is not None
        assert updated_stats.all_time_ranking_position is not None
        assert updated_stats.current_tier is not None
        assert updated_stats.last_updated is not None


@pytest.mark.asyncio
async def test_leaderboard_tier_assignment(sample_leaderboard_stats, test_db):
    """Test that tier badges are assigned correctly based on all-time position."""
    # With only 1 barber in the DB, they should rank #1 → Platinum
    bg_jobs.AsyncSessionLocal = test_db
    try:
        await recalculate_leaderboard_rankings()
    finally:
        from app.core.database import AsyncSessionLocal
        bg_jobs.AsyncSessionLocal = AsyncSessionLocal

    async with test_db() as db:
        result = await db.execute(
            select(BarberLeaderboardStats).where(
                BarberLeaderboardStats.id == sample_leaderboard_stats.id
            )
        )
        stats = result.scalar_one()
        # Single barber is always rank #1 → Platinum (top 10)
        assert stats.current_tier == RankingTier.PLATINUM


@pytest.mark.asyncio
async def test_auto_approve_high_quality_photos(sample_barber, test_db):
    """Test auto-approval of high-quality photos."""
    async with test_db() as db:
        photo = BarberReferencePhoto(
            id="photo-001",
            barber_partner_id=sample_barber.id,
            haircut_type="fade",
            photo_angle="frontal",
            cloudinary_url="https://res.cloudinary.com/test/image.jpg",
            cloudinary_public_id="test/photo-001",
            quality_score=0.85,
            validation_status=PhotoValidationStatus.PENDING,
        )
        db.add(photo)
        await db.commit()

    bg_jobs.AsyncSessionLocal = test_db
    try:
        await auto_approve_high_quality_photos()
    finally:
        from app.core.database import AsyncSessionLocal
        bg_jobs.AsyncSessionLocal = AsyncSessionLocal

    async with test_db() as db:
        result = await db.execute(
            select(BarberReferencePhoto).where(BarberReferencePhoto.id == "photo-001")
        )
        approved_photo = result.scalar_one()

        assert approved_photo.validation_status == PhotoValidationStatus.APPROVED
        assert approved_photo.validated_at is not None


@pytest.mark.asyncio
async def test_auto_approve_skips_low_quality(sample_barber, test_db):
    """Test that low-quality photos (< 0.80) are not auto-approved."""
    async with test_db() as db:
        photo = BarberReferencePhoto(
            id="photo-002",
            barber_partner_id=sample_barber.id,
            haircut_type="fade",
            photo_angle="lateral",
            cloudinary_url="https://res.cloudinary.com/test/image2.jpg",
            cloudinary_public_id="test/photo-002",
            quality_score=0.70,
            validation_status=PhotoValidationStatus.PENDING,
        )
        db.add(photo)
        await db.commit()

    bg_jobs.AsyncSessionLocal = test_db
    try:
        await auto_approve_high_quality_photos()
    finally:
        from app.core.database import AsyncSessionLocal
        bg_jobs.AsyncSessionLocal = AsyncSessionLocal

    async with test_db() as db:
        result = await db.execute(
            select(BarberReferencePhoto).where(BarberReferencePhoto.id == "photo-002")
        )
        photo = result.scalar_one()

        assert photo.validation_status == PhotoValidationStatus.PENDING
        assert photo.validated_at is None


@pytest.mark.asyncio
async def test_auto_approve_respects_existing_status(sample_barber, test_db):
    """Test that already-approved photos are not modified by the auto-approval job."""
    async with test_db() as db:
        original_time = datetime.now(timezone.utc)
        photo = BarberReferencePhoto(
            id="photo-003",
            barber_partner_id=sample_barber.id,
            haircut_type="quiff",
            photo_angle="frontal",
            cloudinary_url="https://res.cloudinary.com/test/image3.jpg",
            cloudinary_public_id="test/photo-003",
            quality_score=0.90,
            validation_status=PhotoValidationStatus.APPROVED,
            validated_at=original_time,
        )
        db.add(photo)
        await db.commit()

    bg_jobs.AsyncSessionLocal = test_db
    try:
        await auto_approve_high_quality_photos()
    finally:
        from app.core.database import AsyncSessionLocal
        bg_jobs.AsyncSessionLocal = AsyncSessionLocal

    async with test_db() as db:
        result = await db.execute(
            select(BarberReferencePhoto).where(BarberReferencePhoto.id == "photo-003")
        )
        photo = result.scalar_one()

        # Already approved — status and timestamp must remain unchanged
        assert photo.validation_status == PhotoValidationStatus.APPROVED
        assert photo.validated_at == original_time

#!/usr/bin/env python3
"""
Development seed: populates stylescan.db with test barbers, leaderboard stats,
and parental consent requests.

Run from stylescan/backend/:
    python seed_db.py
"""
import asyncio
import os
import secrets
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

import app.models  # registers all models with Base.metadata
from app.core.database import Base
from app.models.barber import BarberPartner
from app.models.barber_leaderboard_stats import BarberLeaderboardStats, RankingTier
from app.models.parental_consent_requests import ParentalConsentRequest, ConsentStatus

DATABASE_URL = "sqlite+aiosqlite:///./knowledge_base/stylescan.db"

# (name, barbershop, city, instagram, total_uses, all_time, month, week, tier)
BARBERS = [
    ("Marcos Vidal",     "Barber Kings BCN",      "Barcelona", "marcosvidal.cuts",   87, 87, 32, 12, RankingTier.PLATINUM),
    ("Álvaro Rueda",     "The Shave Club",         "Madrid",    "alvaro_shave",        74, 74, 27,  9, RankingTier.PLATINUM),
    ("Diego Ferrer",     "Corte & Estilo",         "Valencia",  "diegoferrer.barber",  68, 68, 24, 11, RankingTier.PLATINUM),
    ("Iván Castellano",  "Old School Barbería",    "Sevilla",   "ivan.oldschool",      61, 61, 21,  8, RankingTier.PLATINUM),
    ("Jorge Pons",       "Fade Factory",           "Barcelona", "jorge_fades",         52, 52, 19,  7, RankingTier.GOLD),
    ("Raúl Medina",      "The Barber Lounge",      "Madrid",    "raulmedina.cuts",     47, 47, 17,  5, RankingTier.GOLD),
    ("Cristian Roca",    "Gentleman's Cut",        "Zaragoza",  "cristian_gc",         41, 41, 14,  4, RankingTier.GOLD),
    ("Adrián Torres",    "Blade & Brush",          "Valencia",  "adriantorres.b",      35, 35, 12,  3, RankingTier.SILVER),
    ("Pablo Llorente",   "Barbería del Norte",     "Bilbao",    "pablo_norte",         29, 29, 10,  2, RankingTier.SILVER),
    ("Sergio Cano",      "Fine Cut Studio",        "Málaga",    "sergiocano.cuts",     24, 24,  8,  2, RankingTier.SILVER),
    ("Rubén Martí",      "La Barbería",            "Tarragona", "ruben_marti.barber",  16, 16,  5,  1, RankingTier.BRONZE),
    ("Tomás Blanco",     "Nuevo Corte",            "Murcia",    "tomasblanco.nw",      11, 11,  3,  0, RankingTier.BRONZE),
]


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        await db.execute(text("DELETE FROM parental_consent_requests WHERE parent_email LIKE '%@seed.visai.dev'"))
        await db.execute(text("DELETE FROM barber_leaderboard_stats WHERE barber_partner_id IN (SELECT id FROM barber_partners WHERE email LIKE '%@seed.visai.dev')"))
        await db.execute(text("DELETE FROM barber_partners WHERE email LIKE '%@seed.visai.dev'"))
        await db.commit()

        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        barber_ids: list[str] = []

        for i, (name, shop, city, ig, uses, all_time, month, week, tier) in enumerate(BARBERS):
            barber_id = str(uuid.uuid4())
            barber_ids.append(barber_id)
            slug = name.split()[0].lower().replace("á", "a").replace("í", "i").replace("ó", "o").replace("é", "e").replace("ú", "u")
            code = f"VISAI{slug.upper()}{i + 1:02d}"

            db.add(BarberPartner(
                id=barber_id,
                created_at=now - timedelta(days=90 - i * 5),
                name=name,
                barbershop_name=shop,
                email=f"{slug}.{i + 1}@seed.visai.dev",
                phone=f"+3466{60000000 + i}",
                city=city,
                province="España",
                instagram_handle=ig,
                promo_code=code,
                stripe_promo_code_id=f"promo_seed_{i + 1:03d}",
                stripe_coupon_id="coupon_seed_base",
                total_uses=uses,
                total_earned_cents=uses * 300,
                total_paid_out_cents=(uses // 2) * 300,
                is_active=True,
                contract_signed_at=now - timedelta(days=85 - i * 5),
                is_content_creator=i < 3,
                content_bonus_rate=0.10 if i < 3 else 0.0,
            ))

            db.add(BarberLeaderboardStats(
                id=str(uuid.uuid4()),
                created_at=now - timedelta(days=88 - i * 5),
                barber_partner_id=barber_id,
                clients_this_week=week,
                week_start=week_start,
                week_ranking_position=i + 1,
                clients_this_month=month,
                month_start=month_start,
                month_ranking_position=i + 1,
                clients_all_time=all_time,
                all_time_ranking_position=i + 1,
                revenue_this_week_cents=week * 1499,
                revenue_all_time_cents=all_time * 1499,
                current_tier=tier,
                last_updated=now,
            ))

        # Parental consent requests
        pending_id = str(uuid.uuid4())
        db.add(ParentalConsentRequest(
            id=pending_id,
            created_at=now - timedelta(hours=1),
            analysis_id=str(uuid.uuid4()),
            child_age=15,
            parent_email="padre.seed@seed.visai.dev",
            authorization_token=secrets.token_urlsafe(32),
            token_expires_at=now + timedelta(hours=71),
            consent_status=ConsentStatus.PENDING,
            is_authorized=False,
            email_sent_at=now - timedelta(hours=1),
        ))

        db.add(ParentalConsentRequest(
            id=str(uuid.uuid4()),
            created_at=now - timedelta(days=2),
            analysis_id=str(uuid.uuid4()),
            child_age=14,
            parent_email="madre.seed@seed.visai.dev",
            authorization_token=secrets.token_urlsafe(32),
            token_expires_at=now + timedelta(hours=70),
            consent_status=ConsentStatus.AUTHORIZED,
            is_authorized=True,
            authorized_at=now - timedelta(days=1, hours=22),
            email_sent_at=now - timedelta(days=2),
            email_opened_at=now - timedelta(days=1, hours=23),
            email_clicked_at=now - timedelta(days=1, hours=22),
        ))

        await db.commit()

    await engine.dispose()

    print(f"✓ {len(BARBERS)} barberos insertados (4 Platinum · 3 Gold · 3 Silver · 2 Bronze)")
    print(f"✓ 2 consentimientos parentales (1 pendiente · 1 autorizado)")
    first_codes = [
        f"VISAI{BARBERS[i][0].split()[0].upper().replace('Á','A').replace('Í','I').replace('Ó','O')}{i + 1:02d}"
        for i in range(3)
    ]
    print(f"  Ejemplos de código: {', '.join(first_codes)}")


if __name__ == "__main__":
    asyncio.run(seed())

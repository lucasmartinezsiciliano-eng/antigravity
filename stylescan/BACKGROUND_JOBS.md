# VISAI Background Jobs

**Status:** ✅ Implemented  
**Location:** `app/jobs/background_jobs.py`  
**Scheduler:** APScheduler (asyncio)

---

## Jobs Overview

| Job | Schedule | Purpose | Status |
|-----|----------|---------|--------|
| `recalculate_leaderboard_rankings` | Daily 03:00 UTC | Update ranking positions + tier badges | ✅ |
| `auto_approve_high_quality_photos` | Daily 03:00 UTC | Auto-approve reference photos (quality ≥ 0.80) | ✅ |
| `send_weekly_telegram_summary` | Sunday 08:00 UTC | Send Telegram summary to connected barberos | ✅ |
| `_purge_expired_analyses` | Daily 03:00 UTC | Delete analyses past 90-day retention | ✅ (existing) |

---

## Job Details

### 1. Recalculate Leaderboard Rankings

**Schedule:** Daily at 03:00 UTC  
**Function:** `recalculate_leaderboard_rankings()`

**What it does:**
1. Fetches all `BarberLeaderboardStats` records
2. Sorts by:
   - `clients_this_week` → updates `week_ranking_position`
   - `clients_this_month` → updates `month_ranking_position`
   - `clients_all_time` → updates `all_time_ranking_position`
3. Assigns tier badges based on all-time ranking:
   - **Platinum:** Top 10 (position 1-10)
   - **Gold:** Top 11-25 (position 11-25)
   - **Silver:** Top 26-50 (position 26-50)
   - **Bronze:** 51+ (position 51+)
4. Updates `last_updated` timestamp

**Database changes:**
- Updates `week_ranking_position`, `month_ranking_position`, `all_time_ranking_position`
- Updates `current_tier` enum field
- Updates `last_updated` timestamp

**Example scenario:**
```
Monday 03:00 UTC: Rankings recalculated
- Barbero "Juan" has 150 all-time clients → position #5 → Platinum tier
- Barbero "Maria" has 45 all-time clients → position #28 → Silver tier
```

---

### 2. Auto-Approve High-Quality Reference Photos

**Schedule:** Daily at 03:00 UTC  
**Function:** `auto_approve_high_quality_photos()`

**What it does:**
1. Finds all pending reference photos where `quality_score >= 0.80`
2. Sets `validation_status = APPROVED`
3. Sets `validated_at = current_timestamp`

**Criteria:**
- `validation_status == PENDING`
- `quality_score >= 0.80` (MediaPipe confidence threshold)

**Database changes:**
- Updates `validation_status` from PENDING → APPROVED
- Sets `validated_at` timestamp

**Example scenario:**
```
Daily 03:00 UTC: Photo validation
- Photo #123 (quality 0.85) → Auto-approved ✅
- Photo #124 (quality 0.75) → Remains PENDING (manual review needed)
- Photo #125 (quality 0.92) → Auto-approved ✅
```

**Note:** Photos with quality < 0.80 stay PENDING for manual admin review

---

### 3. Send Weekly Telegram Summary

**Schedule:** Sunday at 08:00 UTC  
**Function:** `send_weekly_telegram_summary()`

**What it does:**
1. Finds all Telegram accounts with:
   - `is_connected = True`
   - `notifications_enabled = True`
   - `notify_on_weekly_summary = True`
2. For each account, sends message with:
   - Current week ranking position
   - Current month ranking position
   - All-time ranking position
   - Client counts for each period
   - Current tier badge
3. Updates `last_webhook_delivery_at` and `webhook_delivery_status`
4. Tracks `consecutive_failures` for failed sends

**Message content (Spanish):**
```
📊 RESUMEN SEMANAL VISAI

Tu posición esta semana: #5 🥇 Platinum
Clientes esta semana: 12
Clientes este mes: 45
Clientes totales: 250

🏆 Tu tier: Platinum (Top 10)

¡Sigue así! 💪
```

**Database changes:**
- Updates `last_webhook_delivery_at`
- Updates `webhook_delivery_status` (success/failed)
- Increments `consecutive_failures` on error
- Resets `consecutive_failures` on success

**Example scenario:**
```
Sunday 08:00 UTC: Weekly summaries sent
- Barbero "Juan" (connected) → Message sent ✅
- Barbero "Maria" (not connected) → Skipped
- Barbero "Carlos" (send failed) → consecutive_failures incremented
```

---

## Configuration

All jobs are configured in `app/main.py` during app lifespan startup:

```python
scheduler.add_job(recalculate_leaderboard_rankings, "cron", hour=3, minute=0, id="leaderboard_rankings")
scheduler.add_job(auto_approve_high_quality_photos, "cron", hour=3, minute=0, id="approve_photos")
scheduler.add_job(send_weekly_telegram_summary, "cron", day_of_week=6, hour=8, minute=0, id="telegram_summary")
```

**Timezone:** All jobs run in UTC (APScheduler configured with `timezone="UTC"`)

---

## Error Handling

Each job includes:
- ✅ Try-catch blocks
- ✅ Rollback on database error
- ✅ Detailed logging
- ✅ Exception info logged (not silenced)

**Example:**
```python
try:
    # Job logic
    await db.commit()
    logger.info("Job completed successfully")
except Exception as e:
    logger.error("Error in job: %s", str(e))
    await db.rollback()
```

---

## Monitoring & Debugging

### Check if jobs are running:

```bash
# View logs during startup
tail -f uvicorn.log | grep "APScheduler\|leaderboard\|approve_photos\|telegram_summary"
```

### Test jobs manually (in Python shell):

```python
from app.jobs import recalculate_leaderboard_rankings
import asyncio

asyncio.run(recalculate_leaderboard_rankings())
print("Job executed")
```

### Database queries to verify:

```sql
-- Check latest leaderboard update
SELECT barber_partner_id, current_tier, week_ranking_position, last_updated 
FROM barber_leaderboard_stats 
ORDER BY last_updated DESC 
LIMIT 5;

-- Check auto-approved photos
SELECT COUNT(*), validation_status 
FROM barber_reference_photos 
WHERE validated_at > NOW() - INTERVAL 1 DAY 
GROUP BY validation_status;

-- Check Telegram delivery status
SELECT telegram_user_id, webhook_delivery_status, consecutive_failures, last_webhook_delivery_at 
FROM barber_telegram_accounts 
WHERE is_connected = true 
ORDER BY last_webhook_delivery_at DESC;
```

---

## Known Limitations & Future Work

### MVP Limitations
- ❌ No direct Telegram auto-retry on failure (relies on next week's run)
- ❌ No photo quality threshold adjustment (hardcoded at 0.80)
- ❌ No leaderboard reset logic (week/month resets not auto-triggered)

### Week 2+ Improvements
- ✅ Add weekly/monthly leaderboard reset on Monday 00:00 / 1st of month 00:00
- ✅ Add Telegram auto-retry with exponential backoff
- ✅ Add admin dashboard for monitoring job execution
- ✅ Add metrics/instrumentation for job performance
- ✅ Add configurable quality thresholds per barber

---

## Testing

**Manual test commands:**

```bash
# Start backend with debug logging
RUST_LOG=debug uvicorn app.main:app --reload

# Trigger job manually (if needed)
python -c "
import asyncio
from app.jobs import recalculate_leaderboard_rankings
asyncio.run(recalculate_leaderboard_rankings())
"
```

**Integration test checklist:**
- ✅ Job starts successfully on app startup
- ✅ Leaderboard rankings update correctly
- ✅ Photos auto-approve when quality >= 0.80
- ✅ Telegram messages send to connected barberos
- ✅ Errors are logged but don't crash the app

---

**Generated:** 2026-05-16  
**Status:** Ready for production

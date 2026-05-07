"""
StyleScan — Trend Research Worker

Runs weekly to keep the knowledge base up to date with trending haircut styles.
Can be executed manually or scheduled via APScheduler / cron.

Usage:
  # Run once manually:
  python trend_worker.py

  # Run with APScheduler (every Monday 3am):
  python trend_worker.py --schedule

Requires ANTHROPIC_API_KEY in environment (reads from .env automatically).
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("trend_worker")


def run():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        logger.error("ANTHROPIC_API_KEY not set. Cannot classify trends.")
        sys.exit(1)

    logger.info("Starting trend research run")
    from app.services.trend_service import run_trend_research
    index = run_trend_research(anthropic_key)

    total = sum(len(v) for v in index.get("by_face_shape", {}).values())
    global_count = len(index.get("global_trends", []))
    logger.info("Done. %d shape-specific trends + %d global trends indexed.", total, global_count)


def run_scheduled():
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler()
    # Every Monday at 03:00
    scheduler.add_job(run, "cron", day_of_week="mon", hour=3, minute=0)
    logger.info("Trend worker scheduled: every Monday 03:00. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Trend worker stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StyleScan Trend Research Worker")
    parser.add_argument("--schedule", action="store_true", help="Run on weekly schedule instead of once")
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
    else:
        run()

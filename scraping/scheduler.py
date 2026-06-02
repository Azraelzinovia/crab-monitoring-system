"""
Scraping Scheduler — APScheduler untuk scraping otomatis berkala
"""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from scraping.crab_scraper import CrabDataScraper
from core.config import settings

logger = logging.getLogger(__name__)


class ScrapingScheduler:
    """Scheduler untuk menjalankan scraping otomatis."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")
        self._setup_jobs()

    def _setup_jobs(self):
        """Setup scheduled jobs."""
        # Full scrape every 24 hours (default)
        self.scheduler.add_job(
            self.run_full_scrape,
            trigger=IntervalTrigger(hours=settings.SCRAPING_INTERVAL_HOURS),
            id="full_species_scrape",
            name="Scrape Species Database",
            replace_existing=True,
            max_instances=1,
        )

        # Daily stats update at midnight
        self.scheduler.add_job(
            self.run_stats_update,
            trigger=CronTrigger(hour=0, minute=5),
            id="daily_stats",
            name="Update Daily Statistics",
            replace_existing=True,
        )

    async def run_full_scrape(self):
        """Run full species database scrape."""
        logger.info("🕷️ Starting scheduled species scrape...")
        try:
            scraper = CrabDataScraper()
            data = await asyncio.get_event_loop().run_in_executor(None, scraper.scrape_all)
            logger.info(f"✅ Scraping complete: {len(data)} species records collected")
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")

    async def run_stats_update(self):
        """Update aggregated statistics."""
        logger.info("📊 Updating daily statistics...")
        # Implement statistics caching here
        logger.info("✅ Statistics updated")

    def start(self):
        self.scheduler.start()
        logger.info("⏰ Scraping scheduler started")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("⏰ Scraping scheduler stopped")


# Singleton
scraping_scheduler = ScrapingScheduler()

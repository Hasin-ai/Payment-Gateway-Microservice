import asyncio
import logging
from datetime import datetime

from app.core.database import get_db_session
from app.services.rate_fetcher import RateFetcher
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateUpdater:
    def __init__(self):
        self.running = False
        self.update_interval = settings.RATE_UPDATE_INTERVAL
    
    async def start_periodic_updates(self):
        """Start the periodic rate update task"""
        self.running = True
        logger.info(f"Starting periodic rate updates every {self.update_interval} seconds")
        
        while self.running:
            try:
                await self.update_rates()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                logger.info("Rate updater task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic rate update: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def update_rates(self):
        """Update exchange rates"""
        try:
            db = get_db_session()
            rate_fetcher = RateFetcher(db)
            
            logger.info("Starting scheduled rate update")
            update_result = await rate_fetcher.update_all_rates()
            
            logger.info(
                f"Rate update completed: "
                f"{update_result['successful_updates']} successful, "
                f"{update_result['failed_updates']} failed"
            )
            
            await rate_fetcher.close()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to update rates: {e}")
    
    def stop(self):
        """Stop the periodic updates"""
        self.running = False
        logger.info("Stopping periodic rate updates")

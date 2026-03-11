import asyncio
import httpx
import logging
from src.common.config import settings

logger = logging.getLogger(__name__)

async def self_ping():
    """
    Background task to ping the API periodically to prevent Render from sleeping.
    """
    url = settings.RENDER_EXTERNAL_URL
    if not url:
        logger.info("RENDER_EXTERNAL_URL not set, self-ping disabled.")
        return

    # Ensure the URL is valid
    if not url.startswith("http"):
        url = f"https://{url}" if not "localhost" in url else f"http://{url}"

    logger.info(f"Starting self-ping background task for: {url}")
    
    # Wait a bit after startup before first ping
    await asyncio.sleep(60)
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(url)
                logger.debug(f"Self-ping successful: {response.status_code}")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")
            
            # Ping every 14 minutes (Render free tier sleeps after 15 mins)
            await asyncio.sleep(14 * 60)

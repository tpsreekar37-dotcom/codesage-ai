import redis.asyncio as aioredis
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("app.redis")

redis_client: Optional[aioredis.Redis] = None

async def init_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        try:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5.0,
                retry_on_timeout=True
            )
            # Test connection
            await redis_client.ping()
            logger.info("Successfully connected to Redis cache.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {settings.REDIS_URL}: {str(e)}")
            # Fallback to local process cache or just raising error
            redis_client = None
    return redis_client

async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Closed Redis connection.")
        redis_client = None

def get_redis_client() -> Optional[aioredis.Redis]:
    return redis_client

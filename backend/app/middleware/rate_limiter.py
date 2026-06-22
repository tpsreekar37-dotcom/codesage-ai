import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.redis import get_redis_client

logger = logging.getLogger("app.rate_limiter")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_limit: int = 100):
        super().__init__(app)
        self.requests_limit = requests_limit

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exclude docs and endpoints that don't need rate limiting
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json") or request.url.path.startswith("/redoc"):
            return await call_next(request)
            
        redis = get_redis_client()
        if not redis:
            # If Redis is unavailable, skip rate-limiting (fail open)
            return await call_next(request)
            
        # Get client IP address
        client_ip = request.client.host if request.client else "127.0.0.1"
        current_minute = int(time.time() // 60)
        cache_key = f"rate_limit:{client_ip}:{current_minute}"
        
        try:
            # Increment request count
            count = await redis.incr(cache_key)
            if count == 1:
                # Set TTL of 60 seconds on the first request in the minute window
                await redis.expire(cache_key, 60)
                
            if count > self.requests_limit:
                logger.warning(f"Rate limit exceeded for IP {client_ip} ({count}/{self.requests_limit} requests)")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again in a minute."}
                )
        except Exception as e:
            logger.error(f"Error checking rate limits in Redis: {str(e)}")
            
        return await call_next(request)

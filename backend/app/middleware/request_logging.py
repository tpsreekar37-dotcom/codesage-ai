import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("app.request_logging")
# Basic console logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Log request receipt
        logger.info(f"--> {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = f"{process_time:.2f}ms"
            
            logger.info(
                f"<-- {request.method} {request.url.path} | Status: {response.status_code} | Duration: {formatted_process_time}"
            )
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = f"{process_time:.2f}ms"
            logger.error(
                f"<-- FAIL {request.method} {request.url.path} | Error: {str(e)} | Duration: {formatted_process_time}"
            )
            raise e

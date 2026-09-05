import logging
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

def setup_logging(log_level: str):
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        logger = logging.getLogger("RequestLogger")
        logger.info(f"[{request_id}] Request received: {request.method} {request.url.path}")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[{request_id}] Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} Duration: {process_time_ms:.2f}ms"
            )
            return response
        except Exception as e:
            process_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] Request failed: {request.method} {request.url.path} "
                f"Duration: {process_time_ms:.2f}ms Error: {e}"
            )
            raise

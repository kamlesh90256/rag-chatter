import logging
import uuid
from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .settings import get_settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((perf_counter() - start) * 1000, 2)
            logging.getLogger("rag_platform").info(
                "request_complete",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
        response.headers["x-request-id"] = request_id
        response.headers["x-duration-ms"] = str(duration_ms)
        return response


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

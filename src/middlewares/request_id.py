import time, uuid

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import get_logger
from .logging_ctx import request_id_var

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request_id_var.set(rid)
        start = time.perf_counter()
        resp = await call_next(request)
        dur_ms = round((time.perf_counter() - start) * 1000, 2)
        resp.headers["X-Request-ID"] = rid
        logger.info(
            "http_access",
            method=request.method,
            path=request.url.path,
            status=resp.status_code,
            duration_ms=dur_ms,
            request_id=rid,
        )
        return resp

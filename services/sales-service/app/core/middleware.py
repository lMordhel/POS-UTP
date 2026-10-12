"""Hardening HTTP SPEC-AUTH-002: cabeceras seguras + rate limiting (slowapi)."""
import json
import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import observe

access_logger = logging.getLogger("app.access")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """AC-HARD02-04: cabeceras en todas las respuestas, Server genérico."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Server"] = "POS-UTP"
        return response


def make_limiter() -> Limiter:
    """Limiter por IP en memoria (1 réplica; ver BR-02 de la SPEC)."""
    return Limiter(key_func=get_remote_address)


limiter = make_limiter()


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        {"detail": "límite excedido, reintenta más tarde"},
        status_code=429,
        headers={"Retry-After": "60"},
    )


def _route_template(request: Request) -> str:
    """Identificador estable del endpoint (acotado, sin IDs reales)."""
    endpoint = request.scope.get("endpoint")
    if endpoint is None:
        return "unknown"
    module = getattr(endpoint, "__module__", "") or ""
    qual = getattr(endpoint, "__qualname__", None) or getattr(endpoint, "__name__", "?")
    return f"{module}.{qual}" if module else qual


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """SPEC-OPS-002: request id, métricas y access log JSON. Nunca cambia códigos."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if incoming and len(incoming) <= 128 else uuid.uuid4().hex
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            observe(request.method, _route_template(request), 500, time.perf_counter() - start)
            raise
        duration = time.perf_counter() - start
        route = _route_template(request)
        observe(request.method, route, response.status_code, duration)
        access_logger.info(
            json.dumps(
                {
                    "method": request.method,
                    "route": route,
                    "status": response.status_code,
                    "duration_ms": int(duration * 1000),
                    "request_id": request_id,
                }
            )
        )
        response.headers["X-Request-ID"] = request_id
        return response

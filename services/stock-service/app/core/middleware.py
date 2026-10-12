"""Hardening HTTP SPEC-AUTH-002: cabeceras seguras + rate limiting (slowapi)."""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware


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

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import check_db, get_db, init_db
from app.core.metrics import render as render_metrics
from app.core.middleware import (
    ObservabilityMiddleware,
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_handler,
)

PROD = os.getenv("POS_ENV", "dev") == "prod"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(
    title="POS-UTP stock-service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if PROD else "/docs",
    redoc_url=None if PROD else "/redoc",
    openapi_url=None if PROD else "/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ObservabilityMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health():
    return {"status": "ok", "service": "stock"}


@app.get("/metrics")
def metrics():
    """SPEC-OPS-002: contadores y latencias en formato Prometheus."""
    return PlainTextResponse(render_metrics(), media_type="text/plain; version=0.0.4")


@app.get("/ready")
def ready():
    """SPEC-OPS-002: readiness con chequeo real de DB propia."""
    if not check_db():
        return JSONResponse({"status": "unready"}, status_code=503)
    return {"status": "ok"}

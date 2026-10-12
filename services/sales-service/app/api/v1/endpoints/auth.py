from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.middleware import limiter
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.services.auth_service import (
    InvalidCredentialsError,
    RefreshInvalidError,
    RefreshReuseError,
    login as service_login,
    refresh_pair as service_refresh,
)

router = APIRouter()
_settings = get_settings()


@router.post("/login", response_model=TokenPair)
@limiter.limit(_settings.RATE_LOGIN)
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    """ERF-09 (SPEC-AUTH-001, FR-02). Rate limit SPEC-AUTH-002."""
    try:
        return service_login(db, data.username, data.password)
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "credenciales inválidas")


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(_settings.RATE_REFRESH)
def refresh(request: Request, data: RefreshRequest, db: Session = Depends(get_db)):
    """ERF-09 (SPEC-AUTH-001, FR-07). Rate limit SPEC-AUTH-002."""
    try:
        return service_refresh(db, data.refresh_token)
    except (RefreshInvalidError, RefreshReuseError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "credenciales inválidas")

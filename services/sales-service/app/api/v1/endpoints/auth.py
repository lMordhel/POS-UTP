from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.services.auth_service import (
    InvalidCredentialsError,
    RefreshInvalidError,
    RefreshReuseError,
    login as service_login,
    refresh_pair as service_refresh,
)

router = APIRouter()


@router.post("/login", response_model=TokenPair)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """ERF-09 (SPEC-AUTH-001, FR-02)."""
    try:
        return service_login(db, data.username, data.password)
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "credenciales inválidas")


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """ERF-09 (SPEC-AUTH-001, FR-07)."""
    try:
        return service_refresh(db, data.refresh_token)
    except (RefreshInvalidError, RefreshReuseError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "credenciales inválidas")

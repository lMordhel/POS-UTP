from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_active_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserExistsError
from app.services import user_service as user_service_module

router = APIRouter()
admin_only = require_active_role("admin")


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    """ERF-10 (SPEC-AUTH-001, FR-05). Solo admin."""
    try:
        return user_service_module.create(db, data)
    except UserExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("", response_model=list[UserRead])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    return user_service_module.list_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    found = user_service_module.get(db, user_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return found


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    updated = user_service_module.update(db, user_id, data)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return updated

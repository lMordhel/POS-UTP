from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.middleware import limiter
from app.core.security import require_role
from app.schemas.product import BatchRequest, ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import product_service

router = APIRouter()
admin_only = require_role("admin")
reader = require_role("admin", "cajero")
_settings = get_settings()


def _handle_value_error(exc: ValueError) -> HTTPException:
    if "duplicado" in str(exc):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(_settings.RATE_WRITE)
def create_product(
    request: Request,
    data: ProductCreate,
    db: Session = Depends(get_db),
    _claims: dict = Depends(admin_only),
):
    """ERF-06 (SPEC-STOCK-004). ERF-10: solo admin. Rate limit SPEC-AUTH-002."""
    try:
        return product_service.create(db, data)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.post("/batch", response_model=list[ProductRead])
def batch_products(
    data: BatchRequest,
    db: Session = Depends(get_db),
    _claims: dict = Depends(reader),
):
    """SPEC-STOCK-006: lectura por lote (aditiva). ERF-10: admin y cajero."""
    return product_service.get_batch(db, data.ids)


@router.get("", response_model=list[ProductRead])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = None,
    activo: bool | None = None,
    db: Session = Depends(get_db),
    _claims: dict = Depends(reader),
):
    """ERF-02/08. ERF-10: admin y cajero."""
    return product_service.list_products(db, skip, limit, q, activo)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _claims: dict = Depends(reader),
):
    found = product_service.get(db, product_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found


@router.put("/{product_id}", response_model=ProductRead)
@limiter.limit(_settings.RATE_WRITE)
def update_product(
    request: Request,
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _claims: dict = Depends(admin_only),
):
    """ERF-10: solo admin. Rate limit SPEC-AUTH-002."""
    try:
        found = product_service.update(db, product_id, data)
    except ValueError as exc:
        raise _handle_value_error(exc)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found


@router.delete("/{product_id}", response_model=ProductRead)
@limiter.limit(_settings.RATE_WRITE)
def deactivate_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    _claims: dict = Depends(admin_only),
):
    """ERF-10: solo admin. Rate limit SPEC-AUTH-002."""
    found = product_service.deactivate(db, product_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found

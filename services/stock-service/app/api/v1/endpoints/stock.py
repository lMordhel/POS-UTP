from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.middleware import limiter
from app.core.security import require_role
from app.schemas.stock import StockAdjust, StockRead
from app.services.product_service import (
    InsufficientStockError,
    StockNotFoundError,
    product_service,
)

router = APIRouter()
admin_only = require_role("admin")
reader = require_role("admin", "cajero")
_settings = get_settings()


@router.get("/products/{product_id}/stock", response_model=StockRead)
def get_stock(
    product_id: int,
    db: Session = Depends(get_db),
    _claims: dict = Depends(reader),
):
    """ERF-04 (SPEC-STOCK-002). ERF-10: admin y cajero."""
    found = product_service.get_stock(db, product_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found


@router.patch("/products/{product_id}/stock", response_model=StockRead)
@limiter.limit(_settings.RATE_WRITE)
def adjust_stock(
    request: Request,
    product_id: int,
    data: StockAdjust,
    db: Session = Depends(get_db),
    _claims: dict = Depends(admin_only),
    idempotency_key: str | None = Header(default=None),
):
    """ERF-05 (SPEC-STOCK-003): ajuste por delta, único escritor del inventario. ERF-10: solo admin. Rate limit SPEC-AUTH-002."""
    try:
        return product_service.adjust_stock(
            db,
            product_id,
            data.delta,
            idem_key=idempotency_key,
            actor={"sub": _claims.get("sub", ""), "rol": _claims.get("rol", "")},
            motivo=data.motivo,
        )
    except StockNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )

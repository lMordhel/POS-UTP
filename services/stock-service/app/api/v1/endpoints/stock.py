from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
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
def adjust_stock(
    product_id: int,
    data: StockAdjust,
    db: Session = Depends(get_db),
    _claims: dict = Depends(admin_only),
):
    """ERF-05 (SPEC-STOCK-003): ajuste por delta, único escritor del inventario. ERF-10: solo admin."""
    try:
        return product_service.adjust_stock(db, product_id, data.delta)
    except StockNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.clients.stock_client import StockUnavailableError
from app.core.database import get_db
from app.schemas.sale import SaleCreate, SaleRead
from app.services.sale_service import (
    SaleInsufficientStockError,
    SaleProductNotFoundError,
    SaleService,
    sale_service,
)

router = APIRouter()


def _service() -> SaleService:
    return sale_service


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def register_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    service: SaleService = Depends(_service),
):
    """ERF-01 + ERF-03 (SPEC-SALES-001/002)."""
    try:
        return service.register_sale(db, data)
    except SaleProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SaleInsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except StockUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )


@router.get("", response_model=list[SaleRead])
def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    service: SaleService = Depends(_service),
):
    """ERF-07 (SPEC-SALES-003)."""
    return service.list(db, skip, limit)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    service: SaleService = Depends(_service),
):
    found = service.get(db, sale_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return found

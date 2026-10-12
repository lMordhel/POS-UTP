from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_active_role
from app.clients.stock_client import StockUnavailableError
from app.core.config import get_settings
from app.core.database import get_db
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleRead
from app.services.sale_service import (
    IdempotencyConflictError,
    IdempotencyKeyInvalidError,
    IdempotencyMismatchError,
    SaleInsufficientStockError,
    SaleProductNotFoundError,
    SaleService,
    sale_service,
)

router = APIRouter()
seller = require_active_role("admin", "cajero")
_rate_write = get_settings().RATE_WRITE


def _service() -> SaleService:
    return sale_service


@router.post("", response_model=SaleRead)
@limiter.limit(_rate_write)
def register_sale(
    request: Request,
    response: Response,
    data: SaleCreate,
    db: Session = Depends(get_db),
    service: SaleService = Depends(_service),
    _user: User = Depends(seller),
    idempotency_key: str | None = Header(default=None),
):
    """ERF-01 + ERF-03 (SPEC-SALES-001/002). ERF-10: admin y cajero.

    SPEC-SALES-004: con `Idempotency-Key`, replay → 200 + header,
    mismatch → 422, clave en proceso → 409.
    """
    try:
        sale, replayed = service.register_sale(db, data, idempotency_key=idempotency_key)
    except SaleProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SaleInsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except IdempotencyMismatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except IdempotencyKeyInvalidError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except StockUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )
    if replayed:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotent-Replayed"] = "true"
    else:
        response.status_code = status.HTTP_201_CREATED
    return sale


@router.get("", response_model=list[SaleRead])
def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    service: SaleService = Depends(_service),
    _user: User = Depends(seller),
):
    """ERF-07 (SPEC-SALES-003). ERF-10: admin y cajero en lectura."""
    return service.list(db, skip, limit)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    service: SaleService = Depends(_service),
    _user: User = Depends(seller),
):
    found = service.get(db, sale_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return found

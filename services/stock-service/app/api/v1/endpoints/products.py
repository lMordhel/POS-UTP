from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import product_service

router = APIRouter()


def _handle_value_error(exc: ValueError) -> HTTPException:
    if "duplicado" in str(exc):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    try:
        return product_service.create(db, data)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.get("", response_model=list[ProductRead])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = None,
    activo: bool | None = None,
    db: Session = Depends(get_db),
):
    return product_service.list(db, skip, limit, q, activo)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    found = product_service.get(db, product_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    try:
        found = product_service.update(db, product_id, data)
    except ValueError as exc:
        raise _handle_value_error(exc)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found


@router.delete("/{product_id}", response_model=ProductRead)
def deactivate_product(product_id: int, db: Session = Depends(get_db)):
    found = product_service.deactivate(db, product_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return found

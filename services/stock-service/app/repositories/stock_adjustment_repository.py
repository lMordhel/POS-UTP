"""Acceso a ajustes por clave de idempotencia (SPEC-SALES-004)."""
from sqlalchemy.orm import Session

from app.models.stock_adjustment import StockAdjustment


def get_by_clave(db: Session, clave: str) -> StockAdjustment | None:
    return db.query(StockAdjustment).filter(StockAdjustment.clave == clave).one_or_none()


def create(
    db: Session, clave: str, producto_id: int, delta: int, cantidad_resultante: int
) -> StockAdjustment:
    record = StockAdjustment(
        clave=clave,
        producto_id=producto_id,
        delta=delta,
        cantidad_resultante=cantidad_resultante,
    )
    db.add(record)
    db.flush()
    return record

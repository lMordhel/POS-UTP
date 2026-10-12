"""Acceso a claves de idempotencia (SPEC-SALES-004)."""
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyKey


def get_by_clave(db: Session, clave: str) -> IdempotencyKey | None:
    return db.query(IdempotencyKey).filter(IdempotencyKey.clave == clave).one_or_none()


def create_processing(db: Session, clave: str, cuerpo_hash: str) -> IdempotencyKey:
    record = IdempotencyKey(clave=clave, cuerpo_hash=cuerpo_hash, venta_id=None)
    db.add(record)
    db.flush()
    return record


def complete(db: Session, record: IdempotencyKey, venta_id: int) -> None:
    record.venta_id = venta_id
    db.flush()

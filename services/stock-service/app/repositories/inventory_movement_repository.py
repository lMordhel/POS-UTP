"""Auditoría de movimientos (SPEC-OPS-001, BR-02: solo lectura)."""
from sqlalchemy.orm import Session

from app.models.inventory_movement import InventoryMovement


def record(
    db: Session,
    producto_id: int,
    delta: int,
    cantidad_antes: int,
    cantidad_despues: int,
    motivo: str,
    actor_sub: str,
    actor_rol: str,
    clave: str | None = None,
) -> InventoryMovement:
    movement = InventoryMovement(
        producto_id=producto_id,
        delta=delta,
        cantidad_antes=cantidad_antes,
        cantidad_despues=cantidad_despues,
        motivo=motivo or "",
        actor_sub=actor_sub or "",
        actor_rol=actor_rol or "",
        clave=clave,
    )
    db.add(movement)
    db.flush()
    return movement

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sale import Sale


class SaleRepository:
    def get(self, db: Session, sale_id: int) -> Sale | None:
        return db.get(Sale, sale_id)

    def list(self, db: Session, skip: int, limit: int, desc: bool = True) -> list[Sale]:
        """Lista ventas por id. `desc=True` devuelve la más reciente primero.

        SPEC-SALES-003 1.1.0 (AC-ERF07-04): el orden por defecto es descendente
        porque la vista de supervisión y el punto de venta necesitan la última
        venta registrada en la primera posición.
        """
        order = Sale.id.desc() if desc else Sale.id
        return list(
            db.scalars(select(Sale).order_by(order).offset(skip).limit(limit)).all()
        )


sale_repository = SaleRepository()

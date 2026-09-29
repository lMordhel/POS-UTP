from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sale import Sale


class SaleRepository:
    def get(self, db: Session, sale_id: int) -> Sale | None:
        return db.get(Sale, sale_id)

    def list(self, db: Session, skip: int, limit: int) -> list[Sale]:
        return list(
            db.scalars(select(Sale).order_by(Sale.id).offset(skip).limit(limit)).all()
        )


sale_repository = SaleRepository()

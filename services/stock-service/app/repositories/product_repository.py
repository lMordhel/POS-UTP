from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.product import Product


class ProductRepository:
    def get(self, db: Session, product_id: int) -> Product | None:
        return db.get(Product, product_id)

    def get_by_codigo(self, db: Session, codigo: str) -> Product | None:
        return db.scalars(select(Product).where(Product.codigo == codigo)).first()

    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        q: str | None = None,
        activo: bool | None = None,
    ) -> list[tuple[Product, int]]:
        stmt: Select = (
            select(Product, func.coalesce(Inventory.cantidad, 0))
            .outerjoin(Inventory, Inventory.producto_id == Product.id)
            .order_by(Product.id)
            .offset(skip)
            .limit(limit)
        )
        if q:
            like = f"%{q}%"
            stmt = stmt.where(Product.codigo.ilike(like) | Product.nombre.ilike(like))
        if activo is not None:
            stmt = stmt.where(Product.activo == activo)
        return list(db.execute(stmt).all())

    def get_with_stock(self, db: Session, product_id: int) -> tuple[Product, int] | None:
        row = db.execute(
            select(Product, func.coalesce(Inventory.cantidad, 0))
            .outerjoin(Inventory, Inventory.producto_id == Product.id)
            .where(Product.id == product_id)
        ).first()
        return row if row else None


class InventoryRepository:
    def create_initial(self, db: Session, producto_id: int, cantidad: int) -> Inventory:
        inv = Inventory(producto_id=producto_id, cantidad=cantidad)
        db.add(inv)
        db.flush()
        return inv

    def get_by_product(self, db: Session, producto_id: int) -> Inventory | None:
        return db.scalars(select(Inventory).where(Inventory.producto_id == producto_id)).first()


product_repository = ProductRepository()
inventory_repository = InventoryRepository()

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.product import Product


def locked_inventory_statement(producto_id: int):
    """`SELECT ... FOR UPDATE` de la fila de inventario de un producto (S2).

    Vive a nivel de módulo para que el test pueda compilarlo contra el dialecto
    que aplica el lock (Postgres). SQLite, el motor de la suite, ignora
    `FOR UPDATE` en silencio.
    """
    return select(Inventory).where(Inventory.producto_id == producto_id).with_for_update()


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
        """Lectura sin lock: para consultas y respuestas HTTP (S2)."""
        return db.scalars(select(Inventory).where(Inventory.producto_id == producto_id)).first()

    def get_by_product_for_update(self, db: Session, producto_id: int) -> Inventory | None:
        """Lectura con lock de fila: base del read-modify-write del ajuste (S2).

        Sin esto dos ventas concurrentes del último producto leen la misma
        cantidad y la segunda pisa a la primera (lost update): el
        `CheckConstraint cantidad >= 0` no lo detecta porque cada escritura es
        válida por separado.
        """
        return db.scalars(locked_inventory_statement(producto_id)).first()


product_repository = ProductRepository()
inventory_repository = InventoryRepository()

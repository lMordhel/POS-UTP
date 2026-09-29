from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repository import inventory_repository, product_repository
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.stock import StockRead


def _to_read(product: Product, stock: int) -> ProductRead:
    return ProductRead(
        id=product.id,
        codigo=product.codigo,
        nombre=product.nombre,
        descripcion=product.descripcion,
        precio=product.precio,
        activo=product.activo,
        stock=stock,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


class StockNotFoundError(LookupError):
    pass


class InsufficientStockError(ValueError):
    pass


class ProductService:
    """Business rules for SPEC-STOCK-001/002/003/004/005."""

    def create(self, db: Session, data: ProductCreate) -> ProductRead:
        if product_repository.get_by_codigo(db, data.codigo):
            raise ValueError(f"codigo duplicado: {data.codigo}")
        product = Product(
            codigo=data.codigo,
            nombre=data.nombre,
            descripcion=data.descripcion,
            precio=data.precio,
        )
        db.add(product)
        db.flush()  # assign id before creating inventory row
        inv = inventory_repository.create_initial(db, product.id, data.cantidad_inicial)
        return _to_read(product, inv.cantidad)

    def list(
        self,
        db: Session,
        skip: int,
        limit: int,
        q: str | None,
        activo: bool | None,
    ) -> list[ProductRead]:
        return [_to_read(p, s) for p, s in product_repository.list(db, skip, limit, q, activo)]

    def get(self, db: Session, product_id: int) -> ProductRead | None:
        row = product_repository.get_with_stock(db, product_id)
        return _to_read(row[0], row[1]) if row else None

    def update(self, db: Session, product_id: int, data: ProductUpdate) -> ProductRead | None:
        product = product_repository.get(db, product_id)
        if product is None:
            return None
        patch = data.model_dump(exclude_unset=True)
        if "codigo" in patch and patch["codigo"] != product.codigo:
            if product_repository.get_by_codigo(db, patch["codigo"]):
                raise ValueError(f"codigo duplicado: {patch['codigo']}")
        for field, value in patch.items():
            setattr(product, field, value)
        db.flush()
        inv = inventory_repository.get_by_product(db, product.id)
        return _to_read(product, inv.cantidad if inv else 0)

    def deactivate(self, db: Session, product_id: int) -> ProductRead | None:
        product = product_repository.get(db, product_id)
        if product is None:
            return None
        product.activo = False
        db.flush()
        inv = inventory_repository.get_by_product(db, product.id)
        return _to_read(product, inv.cantidad if inv else 0)

    def get_stock(self, db: Session, product_id: int) -> StockRead | None:
        inv = inventory_repository.get_by_product(db, product_id)
        if inv is None:
            if product_repository.get(db, product_id) is None:
                return None
            return StockRead(producto_id=product_id, cantidad=0, updated_at=None)
        return StockRead(
            producto_id=product_id, cantidad=inv.cantidad, updated_at=inv.updated_at
        )

    def adjust_stock(self, db: Session, product_id: int, delta: int) -> StockRead:
        """SPEC-STOCK-003: único punto de escritura del inventario."""
        inv = inventory_repository.get_by_product(db, product_id)
        if inv is None:
            if product_repository.get(db, product_id) is None:
                raise StockNotFoundError(f"producto inexistente: {product_id}")
            inv = inventory_repository.create_initial(db, product_id, 0)
        new_quantity = inv.cantidad + delta
        if new_quantity < 0:
            raise InsufficientStockError(
                f"stock insuficiente: disponible={inv.cantidad}, delta={delta}"
            )
        inv.cantidad = new_quantity
        db.flush()
        db.refresh(inv)
        return StockRead(
            producto_id=product_id, cantidad=inv.cantidad, updated_at=inv.updated_at
        )


product_service = ProductService()

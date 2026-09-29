from decimal import Decimal

from sqlalchemy.orm import Session

from app.clients.stock_client import (
    StockClient,
    StockInsufficientError,
    StockProductNotFoundError,
    StockUnavailableError,
    stock_client,
)
from app.models.sale import Sale
from app.models.sale_detail import SaleDetail
from app.repositories.sale_repository import sale_repository
from app.schemas.sale import SaleCreate, SaleRead


class SaleProductNotFoundError(LookupError):
    pass


class SaleInsufficientStockError(ValueError):
    pass


class SaleService:
    """Saga registrar-venta (SPEC-SALES-001/002).

    1. Fusiona líneas duplicadas (OQ-ERF03-01 DECIDED).
    2. Resuelve precios oficiales desde Stock (snapshot).
    3. Verifica disponibilidad.
    4. Persiste venta + detalles en ventas_db.
    5. Descuenta stock (delta negativo). Ante fallo: rollback de ventas_db
       (vía excepción) + compensación de descuentos ya aplicados.
    Solo persiste ventas `confirmada` (OQ-ARCH-01 DECIDED).
    """

    def __init__(self, client: StockClient | None = None):
        self.client = client or stock_client

    @staticmethod
    def _merge_items(items: list) -> dict[int, int]:
        merged: dict[int, int] = {}
        for item in items:
            merged[item.producto_id] = merged.get(item.producto_id, 0) + item.cantidad
        return merged

    def register_sale(self, db: Session, data: SaleCreate) -> SaleRead:
        merged = self._merge_items(data.items)

        # 1-2. Precios oficiales + snapshot base.
        prices: dict[int, Decimal] = {}
        for producto_id in merged:
            try:
                product = self.client.get_product(producto_id)
            except StockUnavailableError:
                raise
            except StockProductNotFoundError as exc:
                raise SaleProductNotFoundError(str(exc))
            if not product.activo:
                raise SaleProductNotFoundError(f"producto inactivo: {producto_id}")
            prices[producto_id] = product.precio

        # 3. Disponibilidad.
        for producto_id, cantidad in merged.items():
            try:
                available = self.client.get_stock(producto_id)
            except StockProductNotFoundError as exc:
                raise SaleProductNotFoundError(str(exc))
            if available < cantidad:
                raise SaleInsufficientStockError(
                    f"stock insuficiente producto={producto_id}: "
                    f"disponible={available}, solicitado={cantidad}"
                )

        # 4. Persistir venta + detalles.
        total = sum(prices[pid] * qty for pid, qty in merged.items())
        sale = Sale(total=total, estado="confirmada")
        db.add(sale)
        db.flush()
        for producto_id, cantidad in merged.items():
            subtotal = prices[producto_id] * cantidad
            db.add(
                SaleDetail(
                    venta_id=sale.id,
                    producto_id=producto_id,
                    cantidad=cantidad,
                    precio_unitario=prices[producto_id],
                    subtotal=subtotal,
                )
            )
        db.flush()

        # 5. Descontar stock con compensación ante fallo parcial.
        discounted: list[int] = []
        try:
            for producto_id, cantidad in merged.items():
                self.client.adjust_stock(producto_id, -cantidad, f"venta:{sale.id}")
                discounted.append(producto_id)
        except StockInsufficientError as exc:
            for producto_id in discounted:
                try:
                    self.client.adjust_stock(
                        producto_id, merged[producto_id], f"compensa-venta:{sale.id}"
                    )
                except Exception:
                    pass  # mejor esfuerzo; el rollback de ventas_db ya evita huérfanas
            raise SaleInsufficientStockError(str(exc))
        except StockUnavailableError:
            for producto_id in discounted:
                try:
                    self.client.adjust_stock(
                        producto_id, merged[producto_id], f"compensa-venta:{sale.id}"
                    )
                except Exception:
                    pass
            raise

        db.refresh(sale)
        return SaleRead.model_validate(sale)

    def list(self, db: Session, skip: int, limit: int) -> list[SaleRead]:
        return [SaleRead.model_validate(s) for s in sale_repository.list(db, skip, limit)]

    def get(self, db: Session, sale_id: int) -> SaleRead | None:
        sale = sale_repository.get(db, sale_id)
        return SaleRead.model_validate(sale) if sale else None


sale_service = SaleService()

import hashlib
import json
import logging
import time
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.stock_client import (
    StockClient,
    StockInsufficientError,
    StockUnavailableError,
    stock_client,
)
from app.models.sale import Sale
from app.models.sale_detail import SaleDetail
from app.repositories import idempotency_repository
from app.repositories.sale_repository import sale_repository
from app.schemas.sale import SaleCreate, SaleRead, _normalize_cliente, _normalize_monto

logger = logging.getLogger(__name__)

MAX_KEY_LEN = 64
COMPENSATE_ATTEMPTS = 3


class SaleProductNotFoundError(LookupError):
    pass


class SaleInsufficientStockError(ValueError):
    pass


class SaleInsufficientPaymentError(ValueError):
    """SPEC-SALES-005 FR-04: monto_recibido < total (→ 422, antes de persistir)."""

    pass


class IdempotencyKeyInvalidError(ValueError):
    pass


class IdempotencyMismatchError(ValueError):
    pass


class IdempotencyConflictError(Exception):
    pass


def _body_hash(items: list, cliente: str | None = None, monto: Decimal | None = None) -> str:
    """SPEC-SALES-005 FR-08: el hash cubre items + cliente normalizado + monto."""
    canonical = json.dumps(
        {
            "items": [
                {"producto_id": i.producto_id, "cantidad": i.cantidad}
                for i in sorted(items, key=lambda x: x.producto_id)
            ],
            "cliente": cliente,
            "monto_recibido": str(monto) if monto is not None else None,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


class SaleService:
    """Saga registrar-venta (SPEC-SALES-001/002 + SPEC-SALES-004/005).

    1. Fusiona líneas duplicadas (OQ-ERF03-01 DECIDED).
    2. Resuelve precios oficiales desde Stock (snapshot).
    3. Verifica disponibilidad.
    4. Persiste venta + detalles en ventas_db.
    5. Descuenta stock (delta negativo). Ante fallo: rollback de ventas_db
       (vía excepción) + compensación de descuentos ya aplicados.
    Solo persiste ventas `confirmada` (OQ-ARCH-01 DECIDED).
    Con `Idempotency-Key`: replay/mismatch/concurrente (FR-02..05) y claves
    por línea hacia Stock (FR-06/07/09).
    """

    def __init__(self, client: StockClient | None = None):
        self.client = client or stock_client

    @staticmethod
    def _merge_items(items: list) -> dict[int, int]:
        merged: dict[int, int] = {}
        for item in items:
            merged[item.producto_id] = merged.get(item.producto_id, 0) + item.cantidad
        return merged

    def _compensate(
        self,
        merged: dict[int, int],
        discounted: list[int],
        sale_id: int,
        idempotency_key: str | None,
    ) -> None:
        """Reverso con reintentos; ante fallo final, log estructurado (FR-08)."""
        for producto_id in discounted:
            line_key = f"{idempotency_key}:{producto_id}" if idempotency_key else None
            comp_key = f"{line_key}:compensa" if line_key else None
            for attempt in range(1, COMPENSATE_ATTEMPTS + 1):
                try:
                    self.client.adjust_stock(
                        producto_id,
                        merged[producto_id],
                        f"compensa-venta:{sale_id}",
                        idem_key=comp_key,
                    )
                    break
                except Exception as exc:
                    if attempt >= COMPENSATE_ATTEMPTS:
                        logger.error(
                            "compensación agotada venta=%s producto=%s delta=%s err=%s",
                            sale_id,
                            producto_id,
                            merged[producto_id],
                            exc,
                        )
                    else:
                        time.sleep(0.1 * attempt)

    # Mejora futura (auditoría punto 8, no refactorizar ahora): partir
    # _resolve_key para devolver un resultado tipado (Replay/Nueva/EnProceso)
    # en vez de tupla con string mágico + loop range(2). Cubierto por test_saga.py.
    def _resolve_key(
        self, db: Session, data: SaleCreate, idempotency_key: str | None
    ):
        """Devuelve (record|None, body_hash|None, fresh). Lanza 422/409."""
        if idempotency_key is None:
            return None, None, False
        if not idempotency_key or len(idempotency_key) > MAX_KEY_LEN:
            raise IdempotencyKeyInvalidError("clave de idempotencia inválida")
        body_hash = _body_hash(
            data.items,
            _normalize_cliente(data.cliente),
            _normalize_monto(data.monto_recibido),
        )
        record = None
        fresh = False
        for _ in range(2):
            record = idempotency_repository.get_by_clave(db, idempotency_key)
            if record is not None:
                break
            try:
                record = idempotency_repository.create_processing(
                    db, idempotency_key, body_hash
                )
                db.flush()
                fresh = True
                break
            except IntegrityError:
                db.rollback()
        if record is None:
            raise IdempotencyConflictError("clave en proceso, reintenta")
        if record.venta_id is not None:
            if record.cuerpo_hash != body_hash:
                raise IdempotencyMismatchError("clave reutilizada con otro cuerpo")
            return record, body_hash, "replay"
        if not fresh:
            raise IdempotencyConflictError("clave en proceso, reintenta")
        return record, body_hash, True

    def register_sale(
        self, db: Session, data: SaleCreate, idempotency_key: str | None = None
    ) -> tuple[SaleRead, bool]:
        """Devuelve (venta, replayed). replayed=True solo en replay con clave."""
        record, _, key_state = self._resolve_key(db, data, idempotency_key)
        if key_state == "replay":
            sale = sale_repository.get(db, record.venta_id)
            return SaleRead.model_validate(sale), True

        merged = self._merge_items(data.items)

        # 1-3. Precios oficiales + disponibilidad en una lectura batch (SPEC-STOCK-006).
        try:
            catalog = {p.id: p for p in self.client.batch_get_products(list(merged))}
        except StockUnavailableError:
            raise
        prices: dict[int, Decimal] = {}
        for producto_id, cantidad in merged.items():
            product = catalog.get(producto_id)
            if product is None or not product.activo:
                raise SaleProductNotFoundError(
                    f"producto inexistente o inactivo: {producto_id}"
                )
            prices[producto_id] = product.precio
            if product.stock < cantidad:
                raise SaleInsufficientStockError(
                    f"stock insuficiente producto={producto_id}: "
                    f"disponible={product.stock}, solicitado={cantidad}"
                )

        # 4. Pago en efectivo (SPEC-SALES-005 FR-03/04/05/06): validar ANTES
        # de persistir; vuelto = recibido − total server-side, jamás del request.
        cliente = _normalize_cliente(data.cliente)
        monto = _normalize_monto(data.monto_recibido)
        total = sum(prices[pid] * qty for pid, qty in merged.items())
        if monto is not None and monto < total:
            raise SaleInsufficientPaymentError(
                f"pago insuficiente: recibido={monto}, total={total}"
            )
        vuelto = (monto - total).quantize(Decimal("0.00")) if monto is not None else None

        # 5. Persistir venta + detalles.
        sale = Sale(
            total=total,
            estado="confirmada",
            cliente=cliente,
            monto_recibido=monto,
            vuelto=vuelto,
        )
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

        # 6. Descontar stock con compensación ante fallo parcial.
        discounted: list[int] = []
        try:
            for producto_id, cantidad in merged.items():
                line_key = (
                    f"{idempotency_key}:{producto_id}" if idempotency_key else None
                )
                self.client.adjust_stock(
                    producto_id, -cantidad, f"venta:{sale.id}", idem_key=line_key
                )
                discounted.append(producto_id)
        except StockInsufficientError as exc:
            self._compensate(merged, discounted, sale.id, idempotency_key)
            raise SaleInsufficientStockError(str(exc))
        except StockUnavailableError:
            self._compensate(merged, discounted, sale.id, idempotency_key)
            raise

        db.refresh(sale)
        if record is not None:
            idempotency_repository.complete(db, record, sale.id)
            db.flush()
        return SaleRead.model_validate(sale), False

    def list(self, db: Session, skip: int, limit: int, desc: bool = True) -> list[SaleRead]:
        return [SaleRead.model_validate(s) for s in sale_repository.list(db, skip, limit, desc=desc)]

    def get(self, db: Session, sale_id: int) -> SaleRead | None:
        sale = sale_repository.get(db, sale_id)
        return SaleRead.model_validate(sale) if sale else None


sale_service = SaleService()

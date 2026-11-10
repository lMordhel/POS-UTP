"""L6: dos transacciones crean a la vez la fila de inventario de un producto.

Escenario del defecto: un producto sin fila en `inventories` (solo posible con
datos legados o parciales; `POST /products` la crea). Dos ajustes concurrentes
leen `None` y ambos insertan: el segundo choca contra el `unique` de
`inventories.producto_id` y el `IntegrityError` escapaba como HTTP 500.

Por qué no hay dos hilos: SQLite —el motor de la suite— ignora `FOR UPDATE` en
silencio, así que sus lecturas nunca se serializan y un test con hilos sería
teatro: pasaría igual con y sin el fix. La carrera se reproduce de forma
determinista y con las piezas reales: (1) una segunda Sesión —la transacción que
gana la carrera— confirma la fila antes de que la sesión bajo prueba inserte, y
(2) la lectura obsoleta que el lock debería impedir se inyecta en la primera
llamada a `get_by_product_for_update`. El INSERT siguiente viola el `UNIQUE` de
verdad, sobre la base de datos real y no con un `IntegrityError` fabricado, y el
camino de recuperación encuentra la fila rival ya confirmada, exactamente como
en producción.
"""
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.stock_adjustment import StockAdjustment
from app.repositories.product_repository import inventory_repository
from app.services.product_service import InsufficientStockError, product_service


@pytest.fixture()
def race_db(tmp_path):
    """DB en archivo (en `tmp_path`, fuera del repo) para tener conexiones reales.

    La suite usa `sqlite://` en memoria con `StaticPool`: ahí dos Sesiones
    comparten una sola conexión y con ella la misma transacción, así que no se
    puede simular al ganador de la carrera confirmando su fila. En archivo sí.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'l6.db'}")
    from app.models import (  # noqa: F401 — registra las tablas
        inventory,
        inventory_movement,
        product,
        stock_adjustment,
    )

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield session_factory
    finally:
        engine.dispose()


def _seed_product_without_inventory(session_factory) -> int:
    """Producto legado: existe en `products`, sin fila en `inventories`."""
    with session_factory() as session:
        p = Product(codigo="P-L6", nombre="Producto sin inventario", precio=10)
        session.add(p)
        session.commit()
        return p.id


def _stale_first_locked_read(monkeypatch) -> list[int]:
    """Devuelve `None` en la primera lectura bloqueante (lectura obsoleta).

    Es exactamente lo que la carrera produce en producción: la fila no existía
    cuando esta transacción leyó. Las lecturas posteriores sí ven la realidad,
    así que el reintento del fix es el de verdad.
    """
    calls: list[int] = []
    original = inventory_repository.get_by_product_for_update

    def first_read_stale(db, producto_id):
        calls.append(producto_id)
        if len(calls) == 1:
            return None
        return original(db, producto_id)

    monkeypatch.setattr(inventory_repository, "get_by_product_for_update", first_read_stale)
    return calls


def _competing_session_creates_inventory(session_factory, producto_id: int, cantidad: int) -> None:
    """La transacción rival confirma la fila (lo que provoca el choque del UNIQUE)."""
    with session_factory() as rival:
        rival.add(Inventory(producto_id=producto_id, cantidad=cantidad))
        rival.commit()


def test_adjust_stock_recovers_when_row_is_created_concurrently(race_db, monkeypatch):
    """L6: la fila aparece entre la lectura y el INSERT → no debe estallar.

    El `IntegrityError` del `unique` lo produce la base real; el ajuste debe
    continuar sobre la fila que ganó la carrera y aplicar el delta.
    """
    producto_id = _seed_product_without_inventory(race_db)
    _competing_session_creates_inventory(race_db, producto_id, 0)
    _stale_first_locked_read(monkeypatch)

    with race_db() as db:
        result = product_service.adjust_stock(db, producto_id, 7, motivo="venta:1")
        db.commit()

    assert result.cantidad == 7
    with race_db() as db:
        filas = db.scalars(
            select(Inventory.cantidad).where(Inventory.producto_id == producto_id)
        ).all()
        # Una sola fila de inventario: el INSERT fallido no dejó residuos.
        assert filas == [7]
        movimientos = db.execute(
            select(
                func.count(InventoryMovement.id),
                func.min(InventoryMovement.cantidad_antes),
                func.max(InventoryMovement.cantidad_despues),
            ).where(InventoryMovement.producto_id == producto_id)
        ).one()
        # Un solo movimiento: el que aplicó el delta sobre la fila recuperada.
        assert movimientos == (1, 0, 7)


def test_recovery_keeps_the_callers_unit_of_work(race_db, monkeypatch):
    """L6: la recuperación usa SAVEPOINT, no `rollback()` del caller.

    Un `db.rollback()` completo descartaría el trabajo ya hecho en la misma
    transacción; este test lo demuestra porque el cambio previo debe sobrevivir
    al ajuste.
    """
    producto_id = _seed_product_without_inventory(race_db)
    _competing_session_creates_inventory(race_db, producto_id, 4)
    _stale_first_locked_read(monkeypatch)

    with race_db() as db:
        product = db.get(Product, producto_id)
        product.nombre = "renombrado antes del ajuste"
        db.flush()  # trabajo del caller dentro de la misma unidad de trabajo
        result = product_service.adjust_stock(db, producto_id, 3, motivo="venta:2")
        db.commit()

    # El delta se aplica sobre la cantidad que dejó la transacción rival (4).
    assert result.cantidad == 7
    with race_db() as db:
        assert db.get(Product, producto_id).nombre == "renombrado antes del ajuste"
        inventario = db.scalars(
            select(Inventory.cantidad).where(Inventory.producto_id == producto_id)
        ).all()
        assert inventario == [7]
        assert (
            db.scalar(
                select(func.count(InventoryMovement.id)).where(
                    InventoryMovement.producto_id == producto_id
                )
            )
            == 1
        )


# --- Cierre de huecos de la verificación independiente (L6) ----------------
# Los dos tests de arriba prueban el camino feliz, pero no afirman que el
# reintento ocurrió: si un refactor deja de enrutar por
# `inventory_repository.get_by_product_for_update`, el monkeypatch no aplica, no
# hay lectura obsoleta, no hay choque y siguen en verde sin probar nada. Estos
# cuatro fijan explícitamente el reintento, el re-raise y los dos contratos que
# S3 nombra (idempotencia y 409) sobre la fila recuperada.


def _inventory_rows(session_factory, producto_id):
    with session_factory() as db:
        return db.execute(
            select(Inventory.id, Inventory.cantidad).where(
                Inventory.producto_id == producto_id
            )
        ).all()


def test_recovery_retries_the_read_and_reuses_the_rival_row(race_db, monkeypatch):
    """El reintento ocurre de verdad y termina sobre la fila del rival."""
    producto_id = _seed_product_without_inventory(race_db)
    _competing_session_creates_inventory(race_db, producto_id, 0)
    with race_db() as db:
        rival_id = db.scalars(
            select(Inventory.id).where(Inventory.producto_id == producto_id)
        ).one()

    calls = _stale_first_locked_read(monkeypatch)
    with race_db() as db:
        resultado = product_service.adjust_stock(db, producto_id, 5)
        # El INSERT fallido quedó expurgado: no se re-dispara en un flush posterior.
        assert [o for o in db.new if isinstance(o, Inventory)] == []
        assert db.in_nested_transaction() is False
        assert db.get_transaction().is_active
        db.flush()
        db.commit()

    assert resultado.cantidad == 5
    # Lectura obsoleta + reintento: si el monkeypatch deja de aplicar, esto falla.
    assert len(calls) == 2, calls
    assert _inventory_rows(race_db, producto_id) == [(rival_id, 5)]


def test_unrecoverable_integrity_error_is_reraised_as_is(race_db, monkeypatch):
    """Sin fila rival, el IntegrityError original se re-lanza intacto."""
    producto_id = _seed_product_without_inventory(race_db)
    boom = IntegrityError("INSERT inventory", {}, Exception("simulado"))
    monkeypatch.setattr(
        inventory_repository,
        "create_initial",
        lambda db, producto, cantidad: (_ for _ in ()).throw(boom),
    )

    with race_db() as db:
        with pytest.raises(IntegrityError) as ei:
            product_service.adjust_stock(db, producto_id, 5)
        assert ei.value is boom
        assert db.get_transaction().is_active

    assert _inventory_rows(race_db, producto_id) == []


def test_idempotent_replay_after_recovery_applies_delta_once(race_db, monkeypatch):
    """AC-SAGA04-03 sobre la fila recuperada: el replay no re-aplica el delta."""
    producto_id = _seed_product_without_inventory(race_db)
    _competing_session_creates_inventory(race_db, producto_id, 4)
    _stale_first_locked_read(monkeypatch)

    with race_db() as db:
        assert (
            product_service.adjust_stock(db, producto_id, 3, idem_key="k-l6").cantidad
            == 7
        )
        db.commit()
    with race_db() as db:
        assert (
            product_service.adjust_stock(db, producto_id, 3, idem_key="k-l6").cantidad
            == 7
        )
        db.commit()

    with race_db() as db:
        assert db.scalar(select(func.count(StockAdjustment.id))) == 1
        assert db.scalar(select(func.count(InventoryMovement.id))) == 1
        assert db.scalars(select(Inventory.cantidad)).all() == [7]


def test_insufficient_stock_after_recovery_leaves_no_residue(race_db, monkeypatch):
    """AC-ERF05-03 sobre la fila recuperada: 409 y nada escrito."""
    producto_id = _seed_product_without_inventory(race_db)
    _competing_session_creates_inventory(race_db, producto_id, 4)
    _stale_first_locked_read(monkeypatch)

    with race_db() as db:
        with pytest.raises(InsufficientStockError) as ei:
            product_service.adjust_stock(db, producto_id, -10)
        assert str(ei.value) == "stock insuficiente: disponible=4, delta=-10"
        db.rollback()

    with race_db() as db:
        assert db.scalar(select(func.count(InventoryMovement.id))) == 0
        assert db.scalar(select(func.count(StockAdjustment.id))) == 0
        assert db.scalars(select(Inventory.cantidad)).all() == [4]

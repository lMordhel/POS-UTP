"""Sale contracts (SPEC-SALES-001/002/003 + SPEC-SALES-005, skill pydantic)."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_CLIENTE_LEN = 120


def _normalize_cliente(value: Any) -> str | None:
    """strip(); cadena vacía tras strip() → None; >120 → ValueError (422)."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("cliente debe ser texto o null")
    stripped = value.strip()
    if not stripped:
        return None
    if len(stripped) > MAX_CLIENTE_LEN:
        raise ValueError("cliente supera 120 caracteres")
    return stripped


def _normalize_monto(value: Any) -> Decimal | None:
    """Decimal ≥ 0 con máximo 2 decimales, cuantizado a 2; otro caso → ValueError (422)."""
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("monto_recibido debe ser numérico")
    if amount.is_nan() or amount < 0:
        raise ValueError("monto_recibido debe ser ≥ 0")
    if amount.as_tuple().exponent < -2:
        raise ValueError("monto_recibido admite máximo 2 decimales")
    return amount.quantize(Decimal("0.00"))


class SaleItemIn(BaseModel):
    producto_id: Annotated[int, Field(gt=0)]
    cantidad: Annotated[int, Field(gt=0)]


class SaleCreate(BaseModel):
    """SPEC-SALES-005 FR-01/02: cliente + monto opcionales; vuelto jamás en el request."""

    model_config = ConfigDict(extra="forbid")

    items: Annotated[list[SaleItemIn], Field(min_length=1)]
    cliente: str | None = None
    monto_recibido: Decimal | None = None

    @field_validator("cliente", mode="before")
    @classmethod
    def _norm_cliente(cls, v: Any) -> str | None:
        return _normalize_cliente(v)

    @field_validator("monto_recibido", mode="before")
    @classmethod
    def _norm_monto(cls, v: Any) -> Decimal | None:
        return _normalize_monto(v)


class SaleDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime | None = None
    total: Decimal
    estado: str
    cliente: str | None = None
    monto_recibido: Decimal | None = None
    vuelto: Decimal | None = None
    items: list[SaleDetailRead]

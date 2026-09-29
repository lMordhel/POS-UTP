"""Sale contracts (SPEC-SALES-001/002/003, skill pydantic)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SaleItemIn(BaseModel):
    producto_id: Annotated[int, Field(gt=0)]
    cantidad: Annotated[int, Field(gt=0)]


class SaleCreate(BaseModel):
    items: Annotated[list[SaleItemIn], Field(min_length=1)]


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
    items: list[SaleDetailRead]

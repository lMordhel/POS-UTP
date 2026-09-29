"""Stock contracts (SPEC-STOCK-002/003, skill pydantic: AfterValidator)."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints


def _nonzero(value: int) -> int:
    if value == 0:
        raise ValueError("delta no puede ser 0")
    return value


NonZeroInt = Annotated[int, AfterValidator(_nonzero)]


class StockAdjust(BaseModel):
    """Delta adjustment (APPROVED 2026-09-29, opción B)."""

    delta: NonZeroInt
    motivo: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=120)
    ] = None


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    producto_id: int
    cantidad: int
    updated_at: datetime | None = None

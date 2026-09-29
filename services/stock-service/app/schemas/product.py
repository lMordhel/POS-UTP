"""Product contracts (skill pydantic: Create/Update/Read separados)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Codigo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ProductCreate(BaseModel):
    codigo: Codigo
    nombre: Nombre
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    precio: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
    cantidad_inicial: Annotated[int, Field(ge=0)] = 0


class ProductUpdate(BaseModel):
    """Catalog-only update: cantidad is NOT accepted here (SPEC-STOCK-004 FR-02)."""

    codigo: Codigo | None = None
    nombre: Nombre | None = None
    descripcion: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    precio: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)] | None = None
    activo: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    descripcion: str | None
    precio: Decimal
    activo: bool
    stock: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

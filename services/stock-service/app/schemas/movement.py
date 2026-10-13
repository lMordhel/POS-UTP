"""Movement contracts (SPEC-STOCK-007, skill pydantic)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    codigo: str | None = None
    nombre: str | None = None
    delta: int
    cantidad_antes: int
    cantidad_despues: int
    motivo: str
    actor_sub: str
    actor_rol: str
    clave: str | None = None
    created_at: datetime | None = None

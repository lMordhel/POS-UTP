from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InventoryMovement(Base):
    """Auditoría de ajustes aplicados (SPEC-OPS-001, FR-04). Inmutable."""

    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    producto_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_antes: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_despues: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    codigo: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    nombre: Mapped[str | None] = mapped_column(String(120), nullable=True, default=None)
    actor_sub: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    actor_rol: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    clave: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

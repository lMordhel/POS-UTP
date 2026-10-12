from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IdempotencyKey(Base):
    """Clave de venta (SPEC-SALES-004, FR-02/05). venta_id NULL = en proceso."""

    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    clave: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    cuerpo_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    venta_id: Mapped[int | None] = mapped_column(ForeignKey("sales.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

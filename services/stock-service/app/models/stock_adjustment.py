from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StockAdjustment(Base):
    """Ajuste aplicado por clave (SPEC-SALES-004, FR-07). Replay no re-aplica."""

    __tablename__ = "stock_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    clave: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    producto_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_resultante: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

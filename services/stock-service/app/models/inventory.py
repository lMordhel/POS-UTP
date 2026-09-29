from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Inventory(Base):
    """Stock quantities (SPEC-STOCK-004, ADR-005). Single source of stock truth."""

    __tablename__ = "inventories"
    __table_args__ = (CheckConstraint("cantidad >= 0", name="ck_inventory_cantidad_non_negative"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

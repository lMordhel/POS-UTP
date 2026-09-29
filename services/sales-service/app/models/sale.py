from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Sale(Base):
    """Venta (SPEC-SALES-001). total calculado server-side, sin impuestos."""

    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="confirmada", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["SaleDetail"]] = relationship(
        "SaleDetail", back_populates="sale", cascade="all, delete-orphan"
    )

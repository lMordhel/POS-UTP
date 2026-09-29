from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SaleDetail(Base):
    """Detalle de venta (SPEC-SALES-002). producto_id es referencia lógica a Stock."""

    __tablename__ = "sale_details"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_detail_cantidad_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), index=True, nullable=False
    )
    producto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")

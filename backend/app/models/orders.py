
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    customer = relationship(
        "User",
        foreign_keys=[customer_id],
    )

    # All products included in this order
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    # Legacy single-product fields (kept for compatibility)
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    product_name = Column(String(100), nullable=False)

    quantity = Column(Numeric(10, 3), nullable=False)

    unit_price = Column(Numeric(10, 2), nullable=False)

    # Complete order amount
    total_amount = Column(Numeric(10, 2), nullable=False)

    pickup_time = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    payment_method = Column(
        String(30),
        nullable=False,
        default="COD",
    )

    payment_status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    amount_paid = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    expected_payment_date = Column(
        Date,
        nullable=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def customer_name(self):
        return self.customer.name

    @property
    def customer_phone(self):
        return self.customer.phone

    @property
    def remaining_amount(self):
        total = self.total_amount or 0
        paid = self.amount_paid or 0
        return max(total - paid, 0)

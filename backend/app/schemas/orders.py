
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=3,
    )


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    pickup_time: datetime

    payment_method: Literal["COD", "UPI", "pay_later"] = "COD"

    amount_paid: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=10,
        decimal_places=2,
    )

    expected_payment_date: date | None = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_phone: str

    # Legacy single-product fields, kept for compatibility
    product_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal

    total_amount: Decimal
    pickup_time: datetime
    payment_method: str
    payment_status: str
    amount_paid: Decimal
    expected_payment_date: date | None
    status: str
    created_at: datetime

    # All products in this order
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaymentUpdate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

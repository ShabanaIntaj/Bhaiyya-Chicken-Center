
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class DailySalesCreate(BaseModel):
    sale_date: date
    total_quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=3
    )


class DailySalesResponse(BaseModel):
    id: int
    sale_date: date
    total_quantity: Decimal
    recorded_by: int

    model_config = ConfigDict(from_attributes=True)

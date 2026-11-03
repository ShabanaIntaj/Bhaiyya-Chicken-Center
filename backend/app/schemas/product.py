
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    selling_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    paper_rate: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    is_available: bool = True


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    image_url: str | None = None
    selling_price: Decimal
    is_available: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    selling_price: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    paper_rate: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    is_available: bool | None = None

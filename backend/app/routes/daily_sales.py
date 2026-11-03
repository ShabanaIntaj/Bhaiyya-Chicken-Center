
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.daily_sales import DailySales
from app.models.orders import Order
from app.models.user import User
from app.auth_utils import require_owner
from app.schemas.daily_sales import DailySalesCreate

router = APIRouter(
    prefix="/daily-sales",
    tags=["Daily Sales"]
)


@router.post("/")
def record_daily_sales(
    data: DailySalesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    existing = (
        db.query(DailySales)
        .filter(DailySales.sale_date == data.sale_date)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Daily sales for this date have already been recorded."
        )

    online_quantity = (
        db.query(func.coalesce(func.sum(Order.quantity), 0))
        .filter(
            Order.status == "completed",
            func.date(Order.pickup_time) == data.sale_date
        )
        .scalar()
    )

    online_quantity = Decimal(str(online_quantity))
    total_quantity = data.total_quantity

    if total_quantity < online_quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Total quantity ({total_quantity} kg) cannot be less "
                f"than completed online quantity ({online_quantity} kg)."
            )
        )

    offline_quantity = total_quantity - online_quantity

    record = DailySales(
        sale_date=data.sale_date,
        total_quantity=total_quantity,
        recorded_by=current_user.id
    )

    db.add(record)

    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save daily sales."
        )

    return {
        "message": "Daily sales recorded successfully",
        "sale_date": record.sale_date,
        "total_quantity_kg": total_quantity,
        "online_quantity_kg": online_quantity,
        "offline_quantity_kg": offline_quantity
    }

@router.get("/")
def get_daily_sales(
    sale_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    record = (
        db.query(DailySales)
        .filter(DailySales.sale_date == sale_date)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No daily sales record found for this date."
        )

    online_quantity = (
        db.query(func.coalesce(func.sum(Order.quantity), 0))
        .filter(
            Order.status == "completed",
            func.date(Order.pickup_time) == sale_date
        )
        .scalar()
    )

    
    online_quantity = Decimal(str(online_quantity))
    total_quantity = Decimal(str(record.total_quantity))

    if online_quantity > total_quantity:
        raise HTTPException(
            status_code=409,
            detail=(
                "Completed online quantity exceeds recorded total quantity. "
                "Please review the daily total."
        )
    )

    offline_quantity = total_quantity - online_quantity


    return {
        "sale_date": record.sale_date,
        "total_quantity_kg": total_quantity,
        "online_quantity_kg": online_quantity,
        "offline_quantity_kg": offline_quantity
    }


@router.put("/{sale_date}")
def update_daily_sales(
    sale_date: date,
    data: DailySalesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    record = (
        db.query(DailySales)
        .filter(DailySales.sale_date == sale_date)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No daily sales record found for this date."
        )

    online_quantity = (
        db.query(func.coalesce(func.sum(Order.quantity), 0))
        .filter(
            Order.status == "completed",
            func.date(Order.pickup_time) == sale_date
        )
        .scalar()
    )

    online_quantity = Decimal(str(online_quantity))

    if data.total_quantity < online_quantity:
        raise HTTPException(
            status_code=400,
            detail="Total quantity cannot be less than completed online quantity."
        )

    record.total_quantity = data.total_quantity
    record.recorded_by = current_user.id

    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update daily sales."
        )

    return {
        "message": "Daily sales updated successfully",
        "sale_date": record.sale_date,
        "total_quantity_kg": record.total_quantity,
        "online_quantity_kg": online_quantity,
        "offline_quantity_kg": (
            Decimal(str(record.total_quantity)) - online_quantity
        )
    }


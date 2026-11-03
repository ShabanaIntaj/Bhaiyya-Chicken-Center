
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user, require_owner
from app.database import get_db
from app.models.orders import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.orders import OrderCreate, OrderResponse, PaymentUpdate
from app.shop_settings import ShopSettings
from app.notifications import notification_manager


router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "accepted",
        "preparing",
        "ready",
        "completed",
        "cancelled",
    ]


# Create a new order (customers only)
@router.post("/", response_model=OrderResponse)
def create_order(
    data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only customers can place orders
    if current_user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can place orders",
        )

    # Check whether the shop is open
    shop = (
        db.query(ShopSettings)
        .filter(ShopSettings.id == 1)
        .first()
    )

    if shop is not None and not shop.is_open:
        raise HTTPException(
            status_code=400,
            detail="Shop is currently closed. Please order when it opens.",
        )

    # Check whether the product exists
    product = (
        db.query(Product)
        .filter(Product.id == data.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    if not product.is_available:
        raise HTTPException(
            status_code=400,
            detail="This product is currently unavailable",
        )

    # Pickup time must be in the future
    pickup_time = data.pickup_time

    if pickup_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Please provide pickup_time with a timezone",
        )

    if pickup_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Pickup time must be in the future",
        )

    # Calculate order total using the database selling price per kg
    quantity = data.quantity
    unit_price = Decimal(str(product.selling_price))

    total_amount = (
        quantity * unit_price
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    amount_paid = data.amount_paid

    if amount_paid > total_amount:
        raise HTTPException(
            status_code=400,
            detail="Amount paid cannot exceed the order total",
        )

    if amount_paid > 0 and data.payment_method == "COD":
        raise HTTPException(
            status_code=400,
            detail="For a partial payment, choose UPI or pay_later",
        )

    # Validate pay-later details
    if data.payment_method == "pay_later":
        if not data.expected_payment_date:
            raise HTTPException(
                status_code=400,
                detail="Expected payment date is required for pay later",
            )

        if data.expected_payment_date < pickup_time.date():
            raise HTTPException(
                status_code=400,
                detail="Payment date cannot be before the pickup date",
            )

    # Determine payment status
    if amount_paid >= total_amount:
        payment_status = "paid"
    elif amount_paid > 0:
        payment_status = "partially_paid"
    else:
        payment_status = "pending"

    # Create the order
    order = Order(
        customer_id=current_user.id,
        product_id=product.id,
        product_name=product.name,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        pickup_time=pickup_time,
        payment_method=data.payment_method,
        payment_status=payment_status,
        amount_paid=amount_paid,
        expected_payment_date=data.expected_payment_date,
        status="pending",
    )

    try:
        db.add(order)
        db.commit()
        db.refresh(order)

        background_tasks.add_task(
            notification_manager.broadcast,
            {
                "type": "new_order",
                "order_id": order.id,
                "customer_name": current_user.name,
                "product_name": order.product_name,
                "quantity": str(order.quantity),
                "pickup_time": order.pickup_time.isoformat(),
                "total_amount": str(order.total_amount),
                "status": order.status,
            },
        )

        return order

    except Exception:
            db.rollback()
            raise

# Get orders belonging to the logged-in customer
@router.get("/my", response_model=list[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Order)
        .filter(Order.customer_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


# Owner can view all orders
@router.get("/all", response_model=list[OrderResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
    )

    return [
        {
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": order.customer.name,
            "customer_phone": order.customer.phone,
            "product_id": order.product_id,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "total_amount": order.total_amount,
            "pickup_time": order.pickup_time,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "amount_paid": order.amount_paid,
            "remaining_amount": order.remaining_amount,
            "expected_payment_date": order.expected_payment_date,
            "status": order.status,
            "created_at": order.created_at,
        }
        for order in orders
    ]


# Owner updates order status
@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if order.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="A cancelled order cannot be updated",
        )

    order.status = data.status

    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise


# Owner records an additional payment
@router.patch("/{order_id}/payment", response_model=OrderResponse)
def update_order_payment(
    order_id: int,
    data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    remaining = (
        Decimal(str(order.total_amount))
        - Decimal(str(order.amount_paid))
    )

    if data.amount > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Payment exceeds remaining balance of {remaining}",
        )

    order.amount_paid = (
        Decimal(str(order.amount_paid)) + data.amount
    )

    if order.amount_paid >= order.total_amount:
        order.payment_status = "paid"
    else:
        order.payment_status = "partially_paid"

    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise


# Customer cancels their own pending order; owner can cancel any pending order
@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if (
        current_user.role != "owner"
        and order.customer_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot cancel another customer's order",
        )

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be cancelled",
        )

    if Decimal(str(order.amount_paid)) > 0:
        raise HTTPException(
            status_code=400,
            detail="This order has a payment. Handle the refund before cancellation.",
        )

    order.status = "cancelled"

    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise

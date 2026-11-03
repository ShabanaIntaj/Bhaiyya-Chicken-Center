
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.shop_settings import ShopSettings
from app.models.user import User
from app.auth_utils import require_owner

router = APIRouter(prefix="/shop", tags=["Shop Settings"])


class ShopStatusUpdate(BaseModel):
    status: str


def get_or_create_settings(db: Session):
    settings = db.query(ShopSettings).filter(
        ShopSettings.id == 1
    ).first()

    if settings is None:
        settings = ShopSettings(id=1, is_open=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.get("/status")
def get_shop_status(db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)

    return {
        "status": "open" if settings.is_open else "closed"
    }


@router.patch("/status")
def update_shop_status(
    data: ShopStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    if data.status not in ["open", "closed"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be 'open' or 'closed'"
        )

    settings = get_or_create_settings(db)
    settings.is_open = data.status == "open"

    try:
        db.commit()
        db.refresh(settings)

        return {
            "message": "Shop status updated successfully",
            "status": "open" if settings.is_open else "closed"
        }
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update shop status"
        )

import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.auth_utils import require_owner


router = APIRouter(prefix="/products", tags=["Products"])

# Folder where product images will be saved
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB



@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .order_by(Product.id.desc())
        .all()
    )



@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    existing = db.query(Product).filter(
        Product.name == data.name.strip()
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this name already exists",
        )

    product = Product(
        name=data.name.strip(),
        description=data.description,
        selling_price=data.selling_price,
        paper_rate=data.paper_rate,
        is_available=data.is_available,
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    updates = data.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

        duplicate = db.query(Product).filter(
            Product.name == updates["name"],
            Product.id != product_id,
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another product already uses this name",
            )

    for field, value in updates.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    extension = ALLOWED_TYPES.get(image.content_type)

    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, and WEBP images are allowed",
        )

    content = await image.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 5 MB or smaller",
        )

    # Give the file a unique name instead of trusting its original filename
    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename

    try:
        file_path.write_bytes(content)

        # Save a relative URL in the database
        product.image_url = f"/uploads/products/{filename}"
        db.commit()
        db.refresh(product)

    except Exception:
        if file_path.exists():
            file_path.unlink()
        db.rollback()
        raise

    finally:
        await image.close()

    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Prevent deletion if existing orders reference this product.
    from app.models.orders import Order

    existing_orders = db.query(Order).filter(
        Order.product_id == product_id
    ).first()

    if existing_orders:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product has orders. Mark it unavailable instead.",
        )

    if product.image_url:
        image_path = Path(product.image_url.lstrip("/"))
        if image_path.is_file():
            try:
                image_path.unlink()
            except OSError:
                pass

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


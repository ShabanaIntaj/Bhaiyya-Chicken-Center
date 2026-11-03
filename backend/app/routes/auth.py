
import os
import hmac
import jwt

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from dotenv import load_dotenv

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    CustomerRegister,
    OwnerRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hash = PasswordHash.recommended()


# Create JWT access token
def create_access_token(user: User) -> str:
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret or secret == "replace_with_a_random_secret":
        raise RuntimeError("Set a private JWT_SECRET_KEY in .env")

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expires,
    }

    return jwt.encode(payload, secret, algorithm="HS256")


# Find user using email
def find_user_by_email(db: Session, email: str):
    return db.query(User).filter(
        User.email == email.strip().lower()
    ).first()


# Register a customer or owner
def register_account(db: Session, data, role: str):
    email = data.email.strip().lower()

    if find_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        name=data.name.strip(),
        email=email,
        phone=data.phone.strip(),
        hashed_password=password_hash.hash(data.password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# Customer registration
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_customer(
    data: CustomerRegister,
    db: Session = Depends(get_db),
):
    return register_account(db, data, "customer")


# Owner registration protected by secret PIN
@router.post(
    "/register-owner",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_owner(
    data: OwnerRegister,
    db: Session = Depends(get_db),
):
    configured_pin = os.getenv("OWNER_SECRET_PIN")

    if (
        not configured_pin
        or configured_pin == "CHANGE_THIS_TO_YOUR_PRIVATE_PIN"
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Owner PIN is not configured on the server",
        )

    if not hmac.compare_digest(data.owner_pin, configured_pin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid owner PIN",
        )

    existing_owner = db.query(User).filter(
        User.role == "owner"
    ).first()

    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An owner account already exists",
        )

    return register_account(db, data, "owner")


# Login for customers and owner
@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    user = find_user_by_email(db, data.email)

    if (
        not user
        or not password_hash.verify(
            data.password,
            user.hashed_password,
        )
        or not user.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }

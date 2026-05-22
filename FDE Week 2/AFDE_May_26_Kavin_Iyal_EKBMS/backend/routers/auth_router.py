"""
Authentication endpoints: register, login, password reset, profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_to_response(user: models.User) -> dict:
    """Build a UserResponse dict, populating the role_name."""
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "role_id": user.role_id,
        "role_name": user.role.role_name if user.role else None,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register a new user. Email must be unique."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    role = db.query(models.Role).filter(models.Role.role_name == payload.role.value).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role.value}' does not exist",
        )

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        department=payload.department,
        role_id=role.role_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with email + password. Returns a JWT access token."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled",
        )

    token = create_access_token({"sub": str(user.user_id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_to_response(user),
    }


@router.post("/reset-password", response_model=schemas.UserResponse)
def reset_password(payload: schemas.PasswordReset, db: Session = Depends(get_db)):
    """
    Simple password reset for Phase 1.

    In production this would be gated behind an email-verified token; here
    we just look up the user by email and set the new password. This is
    documented in the requirements as 'Forgot Password' functionality.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this email",
        )
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return _user_to_response(current_user)

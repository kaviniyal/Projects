"""
User management endpoints — admin-only.

Allows admins to list users, change roles, activate/deactivate accounts.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_roles
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


def _user_to_response(user: models.User) -> dict:
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


@router.get("", response_model=List[schemas.UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_roles("Admin")),
):
    """List all users (admin only)."""
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [_user_to_response(u) for u in users]


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a user by ID. Users can view themselves; admins can view anyone."""
    if current_user.user_id != user_id and current_user.role.role_name != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_response(user)


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_roles("Admin")),
):
    """Update a user. Admin only."""
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = payload.model_dump(exclude_unset=True)

    if "role" in data:
        new_role_name = data.pop("role").value if hasattr(data["role"], "value") else data.pop("role")
        role = db.query(models.Role).filter(models.Role.role_name == new_role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{new_role_name}' does not exist")
        user.role_id = role.role_id

    for k, v in data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return _user_to_response(user)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_roles("Admin")),
):
    """Delete a user. Admin only — and admins can't delete themselves."""
    if user_id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}


@router.get("/roles/all", response_model=List[schemas.RoleResponse])
def list_roles(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    """List all available roles."""
    return db.query(models.Role).all()

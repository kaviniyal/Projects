"""
Category management endpoints.

Categories can be nested (hierarchical). Only Admins can create, update,
or delete categories. Anyone authenticated can list them.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_roles
from database import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[schemas.CategoryResponse])
def list_categories(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    """List all categories."""
    return db.query(models.Category).order_by(models.Category.category_name).all()


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    cat = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


@router.post(
    "",
    response_model=schemas.CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("Admin"))],
)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category. Admin only."""
    if payload.parent_id is not None:
        parent = db.query(models.Category).filter(models.Category.category_id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category does not exist")

    cat = models.Category(
        category_name=payload.category_name,
        description=payload.description,
        parent_id=payload.parent_id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put(
    "/{category_id}",
    response_model=schemas.CategoryResponse,
    dependencies=[Depends(require_roles("Admin"))],
)
def update_category(
    category_id: int,
    payload: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
):
    """Update a category. Admin only."""
    cat = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    data = payload.model_dump(exclude_unset=True)

    # Guard against self-parenting
    if data.get("parent_id") == category_id:
        raise HTTPException(status_code=400, detail="A category cannot be its own parent")

    for k, v in data.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete(
    "/{category_id}",
    dependencies=[Depends(require_roles("Admin"))],
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category. Admin only. Fails if articles still reference it."""
    cat = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    article_count = db.query(models.Article).filter(models.Article.category_id == category_id).count()
    if article_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {article_count} article(s) still use this category",
        )

    db.delete(cat)
    db.commit()
    return {"message": f"Category {category_id} deleted"}

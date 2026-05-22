"""
Tag endpoints — list and search tags.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=List[schemas.TagResponse])
def list_tags(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    """List all tags."""
    return db.query(models.Tag).order_by(models.Tag.tag_name).all()

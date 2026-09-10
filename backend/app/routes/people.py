from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/people", tags=["people"])


@router.get("/{user_id}", response_model=schemas.User)
def get_person(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

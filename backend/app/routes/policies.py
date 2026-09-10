from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("/", response_model=List[schemas.Policy])
def get_policies(db: Session = Depends(get_db)):
    """List all workspace policies."""
    return db.query(models.Policy).all()

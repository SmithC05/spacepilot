from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[schemas.CampusEvent])
def get_events(db: Session = Depends(get_db)):
    """List all campus events."""
    return db.query(models.CampusEvent).all()

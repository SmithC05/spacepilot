from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/", response_model=List[schemas.Room])
def get_rooms(db: Session = Depends(get_db)):
    """List all rooms."""
    rooms = db.query(models.Room).all()
    return rooms


@router.get("/{room_id}", response_model=schemas.Room)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a single room by ID."""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Room not found")
    return room

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=List[schemas.Booking])
def get_bookings(db: Session = Depends(get_db)):
    """List all bookings."""
    return db.query(models.Booking).all()


@router.post("/", response_model=schemas.Booking, status_code=201)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    """Create a new booking."""
    db_booking = models.Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.patch("/{booking_id}", response_model=schemas.Booking)
def update_booking(booking_id: int, updates: schemas.BookingUpdate, db: Session = Depends(get_db)):
    """Update an existing booking."""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}", status_code=204)
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    """Delete a booking."""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()

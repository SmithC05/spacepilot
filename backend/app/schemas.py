from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ----- Team -----

class TeamBase(BaseModel):
    name: str

class Team(TeamBase):
    id: int
    model_config = {"from_attributes": True}


# ----- User -----

class UserBase(BaseModel):
    name: str
    email: str
    team_id: Optional[int] = None

class User(UserBase):
    id: int
    model_config = {"from_attributes": True}


# ----- Room -----

class RoomBase(BaseModel):
    name: str
    building: str
    floor: int
    capacity: int
    projector: bool = False
    accessible: bool = False

class Room(RoomBase):
    id: int
    model_config = {"from_attributes": True}


# ----- Booking -----

class BookingCreate(BaseModel):
    room_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None

class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    purpose: Optional[str] = None
    status: Optional[str] = None

class Booking(BaseModel):
    id: int
    room_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: Optional[str]
    status: str
    model_config = {"from_attributes": True}


# ----- CalendarEvent -----

class CalendarEvent(BaseModel):
    id: int
    user_id: int
    title: str
    start_time: datetime
    end_time: datetime
    model_config = {"from_attributes": True}


# ----- CampusEvent -----

class CampusEvent(BaseModel):
    id: int
    name: str
    location: str
    start_time: datetime
    end_time: datetime
    model_config = {"from_attributes": True}


# ----- Policy -----

class Policy(BaseModel):
    id: int
    name: str
    description: str
    model_config = {"from_attributes": True}

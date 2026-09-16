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
    building: Optional[str] = None      # nullable — parsed from node_id prefix
    floor: Optional[int] = None         # nullable — numeric blocks have no floor in ID
    capacity: int
    projector: bool = False
    accessible: bool = False            # maps to wheelchair_accessible in feature data

class Room(RoomBase):
    id: int
    node_id: Optional[str] = None      # spatial graph node link
    x: Optional[float] = None
    y: Optional[float] = None
    ac: bool = False
    projector_type: Optional[str] = None   # "HDMI" | "wireless" | None
    wifi_quality: Optional[str] = None     # poor | average | good | excellent
    whiteboard: bool = False
    computers: int = 0
    noise_level: Optional[str] = None      # quiet | moderate | busy
    booking_restrictions: str = "none"
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

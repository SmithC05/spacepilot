from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    members = relationship("User", back_populates="team")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    team = relationship("Team", back_populates="members")
    bookings = relationship("Booking", back_populates="user")
    calendar_events = relationship("CalendarEvent", back_populates="user")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    building = Column(String, nullable=True)   # nullable — parsed from node_id prefix
    floor = Column(Integer, nullable=True)     # nullable — parsed from node_id prefix
    capacity = Column(Integer, nullable=False)
    projector = Column(Boolean, default=False)
    accessible = Column(Boolean, default=False)  # maps to wheelchair_accessible in feature data

    # Spatial graph link — foreign key into campus_maps.json / room_features.json
    node_id = Column(String, unique=True, index=True, nullable=True)
    x = Column(Float, nullable=True)   # map-coordinate x from campus_maps.json
    y = Column(Float, nullable=True)   # map-coordinate y from campus_maps.json

    # Extended feature columns from room_features.json
    ac = Column(Boolean, default=False)
    projector_type = Column(String, nullable=True)       # "HDMI" | "wireless" | None
    wifi_quality = Column(String, nullable=True)         # poor | average | good | excellent
    whiteboard = Column(Boolean, default=False)
    computers = Column(Integer, default=0)
    noise_level = Column(String, nullable=True)          # quiet | moderate | busy
    booking_restrictions = Column(String, default="none")  # none | staff-only | max-2hr | approval-required

    bookings = relationship("Booking", back_populates="room")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    purpose = Column(String, nullable=True)
    status = Column(String, default="confirmed")  # confirmed | cancelled | pending

    room = relationship("Room", back_populates="bookings")
    user = relationship("User", back_populates="bookings")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="calendar_events")


class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id    = Column(Integer, ForeignKey("teams.id"), nullable=True)
    message    = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)  # stored as ISO 8601 text, matching _ensure_table() DDL


class CampusEvent(Base):
    __tablename__ = "campus_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)

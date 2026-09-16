"""
backend/app/routes/rooms.py

Room endpoints:
  GET /rooms/           — list all rooms (ORM, existing behaviour)
  GET /rooms/available  — filter by feature params (sqlite3, no pydantic needed)
  GET /rooms/{room_id}  — single room by integer PK (ORM, existing behaviour)

NOTE: /rooms/available is declared BEFORE /{room_id} so FastAPI routes it
correctly and doesn't try to cast "available" to an integer.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/rooms", tags=["rooms"])

# Path to the SQLite file — kept consistent with seed.py logic
_DB_FILE = Path(__file__).resolve().parents[2] / "data" / "spacepilot.db"

# Wifi tier ordering for ">= tier" comparisons
_WIFI_TIERS: dict[str, int] = {
    "poor":      0,
    "average":   1,
    "good":      2,
    "excellent": 3,
}


# ---------------------------------------------------------------------------
# GET /rooms/available
# ---------------------------------------------------------------------------

@router.get("/available", tags=["rooms"])
def get_available_rooms(
    min_capacity: Optional[int]  = Query(None, ge=1,   description="Minimum seat capacity"),
    projector:    Optional[bool] = Query(None,          description="Requires projector"),
    accessible:   Optional[bool] = Query(None,          description="Requires wheelchair accessibility"),
    wifi_quality: Optional[str]  = Query(None,          description="Minimum wifi tier: poor|average|good|excellent"),
    ac:           Optional[bool] = Query(None,          description="Requires air conditioning"),
    whiteboard:   Optional[bool] = Query(None,          description="Requires whiteboard"),
    booking_restrictions: Optional[str] = Query(None,  description="Exact match: none|staff-only|max-2hr|approval-required"),
):
    """
    Return rooms that satisfy all supplied filter criteria.

    - All parameters are optional; omitting one means "no constraint on that field".
    - wifi_quality is a *minimum tier* filter: requesting 'good' also returns
      'excellent' rooms (poor < average < good < excellent).
    - booking_restrictions is an exact-match filter.
    - Results include every room feature column so callers can inspect the full record.
    """
    # Validate wifi_quality value early
    if wifi_quality is not None and wifi_quality not in _WIFI_TIERS:
        return JSONResponse(
            status_code=422,
            content={"error": f"Invalid wifi_quality '{wifi_quality}'. Must be one of: poor, average, good, excellent."},
        )

    # Build WHERE clauses dynamically
    clauses: list[str] = []
    params:  list      = []

    if min_capacity is not None:
        clauses.append("capacity >= ?")
        params.append(min_capacity)

    if projector is not None:
        clauses.append("projector = ?")
        params.append(1 if projector else 0)

    if accessible is not None:
        clauses.append("accessible = ?")
        params.append(1 if accessible else 0)

    if ac is not None:
        clauses.append("ac = ?")
        params.append(1 if ac else 0)

    if whiteboard is not None:
        clauses.append("whiteboard = ?")
        params.append(1 if whiteboard else 0)

    if booking_restrictions is not None:
        clauses.append("booking_restrictions = ?")
        params.append(booking_restrictions)

    # wifi_quality: collect all tiers that meet the minimum threshold
    if wifi_quality is not None:
        min_tier = _WIFI_TIERS[wifi_quality]
        matching_tiers = [t for t, rank in _WIFI_TIERS.items() if rank >= min_tier]
        placeholders = ",".join("?" * len(matching_tiers))
        clauses.append(f"wifi_quality IN ({placeholders})")
        params.extend(matching_tiers)

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT
            id, node_id, name, building, floor, x, y,
            capacity, projector, accessible,
            ac, projector_type, wifi_quality,
            whiteboard, computers, noise_level, booking_restrictions
        FROM rooms
        {where_sql}
        ORDER BY building, floor, name
    """

    try:
        con = sqlite3.connect(_DB_FILE)
        con.row_factory = sqlite3.Row
        rows = con.execute(sql, params).fetchall()
        con.close()
    except sqlite3.OperationalError as e:
        return JSONResponse(
            status_code=503,
            content={"error": f"Database error: {e}. Has the seed been run?"},
        )

    # Convert sqlite3.Row → plain dict; cast SQLite integers back to bool
    results = []
    for r in rows:
        d = dict(r)
        d["projector"]  = bool(d["projector"])
        d["accessible"] = bool(d["accessible"])
        d["ac"]         = bool(d["ac"])
        d["whiteboard"] = bool(d["whiteboard"])
        results.append(d)

    filters_applied = {}
    if min_capacity      is not None: filters_applied["min_capacity"]         = min_capacity
    if projector         is not None: filters_applied["projector"]             = projector
    if accessible        is not None: filters_applied["accessible"]            = accessible
    if wifi_quality      is not None: filters_applied["wifi_quality_min_tier"] = wifi_quality
    if ac                is not None: filters_applied["ac"]                    = ac
    if whiteboard        is not None: filters_applied["whiteboard"]            = whiteboard
    if booking_restrictions is not None: filters_applied["booking_restrictions"] = booking_restrictions

    return JSONResponse(content={
        "rooms":           results,
        "total":           len(results),
        "filters_applied": filters_applied,
    })


# ---------------------------------------------------------------------------
# GET /rooms/   — list all (ORM, existing)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.Room])
def get_rooms(db: Session = Depends(get_db)):
    """List all rooms."""
    return db.query(models.Room).all()


# ---------------------------------------------------------------------------
# GET /rooms/{room_id}  — single room by integer PK (ORM, existing)
# ---------------------------------------------------------------------------

@router.get("/{room_id}", response_model=schemas.Room)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a single room by ID."""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Room not found")
    return room

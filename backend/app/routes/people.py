"""
backend/app/routes/people.py

Endpoints:
  GET  /people/{id}                      — person basic info
  GET  /teams/{id}/members               — all members of a team
  GET  /people/{id}/calendar             — user's calendar events (optional ?date=YYYY-MM-DD)
  GET  /teams/{id}/availability          — team-wide free/busy for a window
                                           ?date=YYYY-MM-DD&start_time=HH:MM&end_time=HH:MM

All endpoints use sqlite3 directly (no pydantic/SQLAlchemy ORM dependency needed
while the venv is not yet set up), with JSONResponse for output.
"""

import sqlite3
from datetime import datetime, date as date_type
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(tags=["people"])

_DB_FILE = Path(__file__).resolve().parents[2] / "data" / "spacepilot.db"


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(_DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def _not_found(entity: str, eid: int) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": f"{entity} {eid} not found."})


def _db_error(e: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"error": f"Database error: {e}"})


# ---------------------------------------------------------------------------
# GET /people/{id}
# ---------------------------------------------------------------------------

@router.get("/people/{user_id}", tags=["people"])
def get_person(user_id: int):
    """Return basic info for a single user."""
    try:
        con = _connect()
        row = con.execute(
            "SELECT id, name, email, team_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        con.close()
    except sqlite3.OperationalError as e:
        return _db_error(e)

    if row is None:
        return _not_found("User", user_id)
    return JSONResponse(content=dict(row))


# ---------------------------------------------------------------------------
# GET /teams/{id}/members
# ---------------------------------------------------------------------------

@router.get("/teams/{team_id}/members", tags=["teams"])
def get_team_members(team_id: int):
    """Return all users whose team_id matches the given team."""
    try:
        con = _connect()
        team = con.execute(
            "SELECT id, name FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if team is None:
            con.close()
            return _not_found("Team", team_id)
        members = con.execute(
            "SELECT id, name, email, team_id FROM users WHERE team_id = ?", (team_id,)
        ).fetchall()
        con.close()
    except sqlite3.OperationalError as e:
        return _db_error(e)

    return JSONResponse(content={
        "team_id":   team_id,
        "team_name": team["name"],
        "members":   [dict(m) for m in members],
        "total":     len(members),
    })


# ---------------------------------------------------------------------------
# GET /people/{id}/calendar
# ---------------------------------------------------------------------------

@router.get("/people/{user_id}/calendar", tags=["people"])
def get_person_calendar(
    user_id: int,
    date: Optional[str] = Query(
        None,
        description="Filter to a single day — ISO date: YYYY-MM-DD",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    """
    Return CalendarEvent rows for the given user.
    Optionally filter to events that overlap a specific date.
    """
    try:
        con = _connect()
        user = con.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            con.close()
            return _not_found("User", user_id)

        if date:
            # Events that start on or before end-of-day AND end on or after start-of-day
            day_start = f"{date} 00:00:00"
            day_end   = f"{date} 23:59:59"
            rows = con.execute(
                """
                SELECT id, user_id, title, start_time, end_time
                FROM calendar_events
                WHERE user_id = ?
                  AND start_time <= ?
                  AND end_time   >= ?
                ORDER BY start_time
                """,
                (user_id, day_end, day_start),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT id, user_id, title, start_time, end_time
                FROM calendar_events
                WHERE user_id = ?
                ORDER BY start_time
                """,
                (user_id,),
            ).fetchall()
        con.close()
    except sqlite3.OperationalError as e:
        return _db_error(e)

    return JSONResponse(content={
        "user_id": user_id,
        "date_filter": date,
        "events": [dict(r) for r in rows],
        "total": len(rows),
    })


# ---------------------------------------------------------------------------
# GET /teams/{id}/availability
# ---------------------------------------------------------------------------

@router.get("/teams/{team_id}/availability", tags=["teams"])
def get_team_availability(
    team_id: int,
    date: str = Query(..., description="Date to check: YYYY-MM-DD", regex=r"^\d{4}-\d{2}-\d{2}$"),
    start_time: str = Query(..., description="Window start: HH:MM", regex=r"^\d{2}:\d{2}$"),
    end_time:   str = Query(..., description="Window end:   HH:MM", regex=r"^\d{2}:\d{2}$"),
):
    """
    Check whether every member of the team is free (no overlapping CalendarEvent)
    in the given window. Returns per-member conflict details if any exist.

    Query params:
      date       YYYY-MM-DD
      start_time HH:MM
      end_time   HH:MM
    """
    window_start_str = f"{date} {start_time}:00"
    window_end_str   = f"{date} {end_time}:00"

    # Validate ordering
    try:
        window_start = datetime.strptime(window_start_str, "%Y-%m-%d %H:%M:%S")
        window_end   = datetime.strptime(window_end_str,   "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return JSONResponse(status_code=422, content={"error": f"Invalid date/time: {e}"})

    if window_end <= window_start:
        return JSONResponse(status_code=422, content={"error": "end_time must be after start_time."})

    try:
        con = _connect()
        team = con.execute("SELECT id, name FROM teams WHERE id = ?", (team_id,)).fetchone()
        if team is None:
            con.close()
            return _not_found("Team", team_id)

        members = con.execute(
            "SELECT id, name, email FROM users WHERE team_id = ?", (team_id,)
        ).fetchall()

        member_results = []
        all_free = True

        for member in members:
            uid = member["id"]
            # Overlap: event.start < window.end AND event.end > window.start
            conflicts = con.execute(
                """
                SELECT id, title, start_time, end_time
                FROM calendar_events
                WHERE user_id = ?
                  AND start_time < ?
                  AND end_time   > ?
                ORDER BY start_time
                """,
                (uid, window_end_str, window_start_str),
            ).fetchall()

            is_free = len(conflicts) == 0
            if not is_free:
                all_free = False

            member_results.append({
                "user_id":   uid,
                "name":      member["name"],
                "email":     member["email"],
                "free":      is_free,
                "conflicts": [dict(c) for c in conflicts],
            })

        con.close()
    except sqlite3.OperationalError as e:
        return _db_error(e)

    return JSONResponse(content={
        "team_id":      team_id,
        "team_name":    team["name"],
        "date":         date,
        "start_time":   start_time,
        "end_time":     end_time,
        "all_members_free": all_free,
        "member_count": len(member_results),
        "members":      member_results,
    })

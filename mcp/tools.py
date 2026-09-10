"""
SpacePilot MCP Tools

Each function here is registered as an MCP tool in server.py.
Tools call the backend REST API over HTTP — they never touch the database directly.

Phase 1 (implemented with real logic):
    find_rooms, get_room_details, check_room_availability,
    get_route, get_accessible_route

Phase 2 (functional stubs — delegate to backend or return structured placeholder):
    get_events, check_policy, create_booking, update_booking,
    cancel_booking, check_team_availability, notify_team
"""

import os
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv

from navigation import get_route_between

load_dotenv()

BACKEND_URL  = os.getenv("BACKEND_URL", "http://localhost:8000")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10.0"))


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

class BackendError(Exception):
    """Raised when the backend cannot be reached or returns an error."""


def _get(path: str, params: dict = None):
    """GET request to the backend. Raises BackendError on failure."""
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            r = client.get(f"{BACKEND_URL}{path}", params=params)
            if r.status_code == 404:
                raise BackendError(f"Not found: {path}")
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        raise BackendError(
            f"Cannot connect to backend at {BACKEND_URL}. "
            "Make sure the backend is running (uvicorn app.main:app --port 8000)."
        )
    except httpx.TimeoutException:
        raise BackendError(
            f"Backend request timed out after {HTTP_TIMEOUT}s: GET {path}"
        )
    except httpx.HTTPStatusError as e:
        raise BackendError(
            f"Backend returned HTTP {e.response.status_code}: {e.response.text[:300]}"
        )


def _post(path: str, body: dict) -> dict:
    """POST request to the backend. Raises BackendError on failure."""
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            r = client.post(f"{BACKEND_URL}{path}", json=body)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        raise BackendError(f"Cannot connect to backend at {BACKEND_URL}.")
    except httpx.TimeoutException:
        raise BackendError(f"Backend request timed out after {HTTP_TIMEOUT}s.")
    except httpx.HTTPStatusError as e:
        raise BackendError(f"Backend returned HTTP {e.response.status_code}: {e.response.text[:300]}")


def _patch(path: str, body: dict) -> dict:
    """PATCH request to the backend. Raises BackendError on failure."""
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            r = client.patch(f"{BACKEND_URL}{path}", json=body)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        raise BackendError(f"Cannot connect to backend at {BACKEND_URL}.")
    except httpx.TimeoutException:
        raise BackendError(f"Backend request timed out after {HTTP_TIMEOUT}s.")
    except httpx.HTTPStatusError as e:
        raise BackendError(f"Backend returned HTTP {e.response.status_code}: {e.response.text[:300]}")


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

_DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
]


def _parse_dt(value: str, field: str) -> datetime:
    """
    Parse an ISO-ish datetime string.
    Accepts: YYYY-MM-DDTHH:MM, YYYY-MM-DDTHH:MM:SS, and space-separated variants.
    Raises ValueError with a helpful message on failure.
    """
    # Strip microseconds returned by the backend (e.g. "2024-11-15T16:00:00.000000")
    value = value.split(".")[0]
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Invalid {field}: '{value}'. "
        "Use ISO 8601 format — e.g. 2024-11-15T16:00 or 2024-11-15T16:00:00"
    )


def _overlaps(b_start_str: str, b_end_str: str, req_start: datetime, req_end: datetime) -> bool:
    """Return True if a booking [b_start, b_end] overlaps the request window [req_start, req_end]."""
    b_start = _parse_dt(b_start_str, "booking start_time")
    b_end   = _parse_dt(b_end_str,   "booking end_time")
    # Standard interval overlap: A.start < B.end AND A.end > B.start
    return b_start < req_end and b_end > req_start


# ---------------------------------------------------------------------------
# Phase 1 — Room tools
# ---------------------------------------------------------------------------

def find_rooms(
    capacity: int = None,
    start_datetime: str = None,
    end_datetime: str = None,
    projector_required: bool = False,
    accessible_required: bool = False,
) -> dict:
    """
    Return rooms that match the given criteria.

    - Attribute filters (capacity, projector, accessible) are applied first.
    - If start_datetime and end_datetime are both given, rooms with conflicting
      confirmed bookings are excluded.

    Returns:
        {
            "rooms": [...],
            "total": int,
            "filters_applied": [str, ...],
            "availability_checked": bool
        }
    """
    # --- Validate inputs ---
    if capacity is not None:
        if not isinstance(capacity, int) or capacity < 1:
            return {
                "error": f"capacity must be a positive integer, got {capacity!r}",
                "rooms": [], "total": 0,
            }

    req_start: Optional[datetime] = None
    req_end:   Optional[datetime] = None

    if start_datetime is not None or end_datetime is not None:
        if not start_datetime or not end_datetime:
            return {
                "error": "Both start_datetime and end_datetime must be provided together.",
                "rooms": [], "total": 0,
            }
        try:
            req_start = _parse_dt(start_datetime, "start_datetime")
            req_end   = _parse_dt(end_datetime,   "end_datetime")
        except ValueError as e:
            return {"error": str(e), "rooms": [], "total": 0}
        if req_end <= req_start:
            return {
                "error": "end_datetime must be after start_datetime.",
                "rooms": [], "total": 0,
            }

    # --- Fetch all rooms ---
    try:
        rooms = _get("/rooms")
    except BackendError as e:
        return {"error": str(e), "rooms": [], "total": 0}

    if not isinstance(rooms, list):
        return {
            "error": "Unexpected response from /rooms — expected a JSON array.",
            "rooms": [], "total": 0,
        }

    # --- Attribute filters ---
    filters_applied = []

    if capacity is not None:
        rooms = [r for r in rooms if r.get("capacity", 0) >= capacity]
        filters_applied.append(f"capacity >= {capacity}")

    if projector_required:
        rooms = [r for r in rooms if r.get("projector") is True]
        filters_applied.append("projector = true")

    if accessible_required:
        rooms = [r for r in rooms if r.get("accessible") is True]
        filters_applied.append("accessible = true")

    # --- Availability filter ---
    availability_checked = False

    if req_start and req_end:
        try:
            all_bookings = _get("/bookings")
            availability_checked = True

            # Find rooms that have a confirmed booking overlapping the window
            unavailable_room_ids: set[int] = set()
            for booking in all_bookings:
                if booking.get("status") == "cancelled":
                    continue
                try:
                    if _overlaps(
                        booking["start_time"],
                        booking["end_time"],
                        req_start,
                        req_end,
                    ):
                        unavailable_room_ids.add(booking["room_id"])
                except (KeyError, ValueError):
                    continue  # skip malformed booking records

            rooms = [r for r in rooms if r.get("id") not in unavailable_room_ids]
            filters_applied.append(
                f"available {start_datetime} to {end_datetime}"
            )

        except BackendError:
            # Cannot check availability — still return attribute-filtered rooms
            filters_applied.append("availability check skipped (backend unavailable)")

    return {
        "rooms":                rooms,
        "total":                len(rooms),
        "filters_applied":      filters_applied,
        "availability_checked": availability_checked,
    }


def get_room_details(room_id: int) -> dict:
    """
    Return full details for a single room by its integer database ID.
    Returns an error dict if the room does not exist.
    """
    if not isinstance(room_id, int) or room_id < 1:
        return {"error": f"room_id must be a positive integer, got {room_id!r}"}
    try:
        return _get(f"/rooms/{room_id}")
    except BackendError as e:
        return {"error": str(e)}


def check_room_availability(room_id: int, start_datetime: str, end_datetime: str) -> dict:
    """
    Check whether a specific room is free during a time window.

    Returns:
        {
            "room_id": int,
            "room_name": str,
            "building": str,
            "floor": int,
            "start_datetime": str,
            "end_datetime": str,
            "available": bool,
            "conflicts": [{ booking_id, start_time, end_time, purpose, status }],
            "conflict_count": int
        }
    """
    if not isinstance(room_id, int) or room_id < 1:
        return {"error": f"room_id must be a positive integer, got {room_id!r}"}

    try:
        req_start = _parse_dt(start_datetime, "start_datetime")
        req_end   = _parse_dt(end_datetime,   "end_datetime")
    except ValueError as e:
        return {"error": str(e)}

    if req_end <= req_start:
        return {"error": "end_datetime must be after start_datetime."}

    # Confirm the room exists
    try:
        room = _get(f"/rooms/{room_id}")
    except BackendError as e:
        return {"error": str(e)}

    # Fetch bookings and filter for conflicts
    try:
        all_bookings = _get("/bookings")
    except BackendError as e:
        return {"error": f"Cannot check availability: {e}"}

    conflicts = []
    for booking in all_bookings:
        if booking.get("room_id") != room_id:
            continue
        if booking.get("status") == "cancelled":
            continue
        try:
            if _overlaps(booking["start_time"], booking["end_time"], req_start, req_end):
                conflicts.append({
                    "booking_id": booking["id"],
                    "start_time": booking["start_time"],
                    "end_time":   booking["end_time"],
                    "purpose":    booking.get("purpose"),
                    "status":     booking.get("status"),
                })
        except (KeyError, ValueError):
            continue

    return {
        "room_id":        room_id,
        "room_name":      room.get("name"),
        "building":       room.get("building"),
        "floor":          room.get("floor"),
        "capacity":       room.get("capacity"),
        "projector":      room.get("projector"),
        "accessible":     room.get("accessible"),
        "start_datetime": start_datetime,
        "end_datetime":   end_datetime,
        "available":      len(conflicts) == 0,
        "conflicts":      conflicts,
        "conflict_count": len(conflicts),
    }


# ---------------------------------------------------------------------------
# Phase 1 — Navigation tools
# ---------------------------------------------------------------------------

def get_route(from_room: str, to_room: str) -> dict:
    """
    Get step-by-step walking directions between two campus rooms.
    Uses the FindMyCampus spatial graph (Dijkstra shortest path).
    """
    if not from_room or not isinstance(from_room, str):
        return {"error": "from_room must be a non-empty string (e.g. '201', 'A101')."}
    if not to_room or not isinstance(to_room, str):
        return {"error": "to_room must be a non-empty string (e.g. '302', 'B101')."}

    return get_route_between(from_room.strip(), to_room.strip(), accessible=False)


def get_accessible_route(from_room: str, to_room: str) -> dict:
    """
    Get an accessible (wheelchair-friendly) route between two campus rooms.
    Flags routes that include stairs and warns if no stair-free path exists.
    """
    if not from_room or not isinstance(from_room, str):
        return {"error": "from_room must be a non-empty string."}
    if not to_room or not isinstance(to_room, str):
        return {"error": "to_room must be a non-empty string."}

    return get_route_between(from_room.strip(), to_room.strip(), accessible=True)


# ---------------------------------------------------------------------------
# Phase 2 — Events and Policy (functional, delegate to backend)
# ---------------------------------------------------------------------------

def get_events() -> list:
    """Return all upcoming campus events."""
    try:
        return _get("/events")
    except BackendError as e:
        return [{"error": str(e)}]


def check_policy(query: str = None) -> list:
    """Return workspace policies, optionally filtered by keyword."""
    try:
        policies = _get("/policies")
    except BackendError as e:
        return [{"error": str(e)}]

    if query:
        q = query.lower()
        policies = [
            p for p in policies
            if q in p.get("name", "").lower() or q in p.get("description", "").lower()
        ]
    return policies


# ---------------------------------------------------------------------------
# Phase 2 — Booking tools (fully functional — delegate to backend)
# ---------------------------------------------------------------------------

def create_booking(
    room_id: int,
    user_id: int,
    start_time: str,
    end_time: str,
    purpose: str = None,
) -> dict:
    """Create a new room booking."""
    try:
        return _post("/bookings", {
            "room_id":    room_id,
            "user_id":    user_id,
            "start_time": start_time,
            "end_time":   end_time,
            "purpose":    purpose,
        })
    except BackendError as e:
        return {"error": str(e)}


def update_booking(
    booking_id: int,
    start_time: str = None,
    end_time: str = None,
    purpose: str = None,
) -> dict:
    """Update an existing booking's time slot or purpose."""
    updates = {}
    if start_time:
        updates["start_time"] = start_time
    if end_time:
        updates["end_time"] = end_time
    if purpose:
        updates["purpose"] = purpose
    if not updates:
        return {
            "error": "Nothing to update. Provide at least one of: start_time, end_time, purpose."
        }
    try:
        return _patch(f"/bookings/{booking_id}", updates)
    except BackendError as e:
        return {"error": str(e)}


def cancel_booking(booking_id: int) -> dict:
    """Cancel a booking by setting its status to 'cancelled'."""
    try:
        return _patch(f"/bookings/{booking_id}", {"status": "cancelled"})
    except BackendError as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Phase 2 — Team / notification tools (stubs with clear integration notes)
# ---------------------------------------------------------------------------

def check_team_availability(team_id: int, start_time: str, end_time: str) -> dict:
    """
    Check which team members are free for a given time window.

    STUB — requires the backend to expose calendar endpoints:
        GET /teams/{team_id}/members
        GET /people/{user_id}/calendar or GET /calendar-events?user_id=X
    The backend team must implement these before this tool can return real data.
    """
    return {
        "team_id":           team_id,
        "start_time":        start_time,
        "end_time":          end_time,
        "available_members": [],
        "note": (
            "Team availability check is not yet implemented. "
            "Requires backend endpoints: GET /teams/{id}/members and "
            "calendar event filtering by user. See integration notes."
        ),
    }


def notify_team(team_id: int, message: str) -> dict:
    """
    Notify all members of a team with a message.

    STUB — no notification service integrated yet.
    Logs the intent; actual delivery requires an email/push/Slack integration.
    """
    return {
        "team_id": team_id,
        "message": message,
        "sent":    False,
        "note":    "Notification delivery not yet implemented. Message logged only.",
    }

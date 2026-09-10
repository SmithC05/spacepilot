"""
SpacePilot MCP Server

Exposes SpacePilot campus operations as AI-callable tools.

Transport : Streamable HTTP (MCP specification 2025-11-25+)
Default   : http://0.0.0.0:8080/mcp
Alexa+    : Connect via Streamable HTTP to the /mcp endpoint

Run:
    python server.py

Environment variables (see .env.example):
    MCP_HOST      — bind address (default: 0.0.0.0)
    MCP_PORT      — listen port  (default: 8080)
    BACKEND_URL   — SpacePilot backend (default: http://localhost:8000)
    HTTP_TIMEOUT  — backend request timeout in seconds (default: 10.0)
"""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

import tools as spacepilot_tools

load_dotenv()

HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8080"))

# ---------------------------------------------------------------------------
# Create FastMCP instance
# host and port are consumed by run_streamable_http_async → uvicorn
# ---------------------------------------------------------------------------

mcp = FastMCP("SpacePilot", host=HOST, port=PORT)


# ===========================================================================
# Phase 1 tools — implemented and tested
# ===========================================================================

@mcp.tool()
def find_rooms(
    capacity: int = None,
    start_datetime: str = None,
    end_datetime: str = None,
    projector_required: bool = False,
    accessible_required: bool = False,
) -> dict:
    """
    Find campus rooms that match the given requirements.

    Use this when the user asks to find a room, search for available spaces,
    or needs a room with specific features (projector, wheelchair access).

    If start_datetime and end_datetime are provided, rooms with confirmed
    bookings that overlap the requested window are excluded. Check
    availability_checked in the response to confirm whether this filter ran.

    Do NOT claim a room is available if availability_checked is false.

    Args:
        capacity: Minimum number of people the room must seat (positive integer).
        start_datetime: Start of the required time slot — ISO 8601, e.g. 2024-11-15T16:00
        end_datetime: End of the required time slot — ISO 8601, e.g. 2024-11-15T17:00
        projector_required: True if a projector is needed.
        accessible_required: True if wheelchair accessibility is required.

    Returns:
        {
            "rooms": [ { id, name, building, floor, capacity, projector, accessible } ],
            "total": int,
            "filters_applied": [str],
            "availability_checked": bool
        }
        or { "error": "...", "rooms": [], "total": 0 } on failure.
    """
    return spacepilot_tools.find_rooms(
        capacity=capacity,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        projector_required=projector_required,
        accessible_required=accessible_required,
    )


@mcp.tool()
def get_room_details(room_id: int) -> dict:
    """
    Get full details for a specific campus room by its integer database ID.

    Use after find_rooms to inspect a specific room before booking it.

    Args:
        room_id: Integer room ID returned by find_rooms.

    Returns:
        { id, name, building, floor, capacity, projector, accessible }
        or { "error": "..." } if the room does not exist or the backend is unavailable.
    """
    return spacepilot_tools.get_room_details(room_id)


@mcp.tool()
def check_room_availability(
    room_id: int,
    start_datetime: str,
    end_datetime: str,
) -> dict:
    """
    Check whether a specific room is free during a requested time window.

    Call this before creating a booking to confirm there is no conflict.
    Checks all non-cancelled bookings for the room in the given window.

    Args:
        room_id: Integer room ID to check.
        start_datetime: Start time — ISO 8601, e.g. 2024-11-15T16:00
        end_datetime: End time — ISO 8601, e.g. 2024-11-15T17:00

    Returns:
        {
            "room_id": int, "room_name": str, "building": str, "floor": int,
            "capacity": int, "projector": bool, "accessible": bool,
            "start_datetime": str, "end_datetime": str,
            "available": bool,
            "conflicts": [ { booking_id, start_time, end_time, purpose, status } ],
            "conflict_count": int
        }
        or { "error": "..." } on failure.
    """
    return spacepilot_tools.check_room_availability(room_id, start_datetime, end_datetime)


@mcp.tool()
def get_route(from_room: str, to_room: str) -> dict:
    """
    Get step-by-step walking directions between two campus rooms.

    Uses the FindMyCampus spatial graph to compute the shortest path via
    Dijkstra's algorithm. Works for rooms within the same building floor.
    Cross-building routes return a simplified path with a guidance note.

    Args:
        from_room: Room name or number as shown on campus maps — e.g. "201", "A101", "F4".
        to_room: Destination room name or number.

    Returns:
        {
            "from_room": str, "to_room": str,
            "steps": [ { "step": int, "instruction": str, "node_id": str } ],
            "distance_units": float,
            "map": str,
            "has_stairs": bool
        }
        or { "error": "..." } if either room is not found.
    """
    return spacepilot_tools.get_route(from_room, to_room)


@mcp.tool()
def get_accessible_route(from_room: str, to_room: str) -> dict:
    """
    Get an accessible (wheelchair-friendly) route between two campus rooms.

    Same as get_route, but flags routes that include stairs and adds an
    accessibility_warning if no stair-free alternative is available.
    Always prefer this tool when the user has an accessibility requirement.

    Args:
        from_room: Starting room name or number — e.g. "201", "A101".
        to_room: Destination room name or number.

    Returns:
        Same structure as get_route, with additional fields:
        "has_stairs": bool
        "accessible": bool
        "accessibility_warning": str (only present if stairs cannot be avoided)
    """
    return spacepilot_tools.get_accessible_route(from_room, to_room)


# ===========================================================================
# Phase 2 tools — functional where backend supports them, stubs otherwise
# ===========================================================================

@mcp.tool()
def check_team_availability(team_id: int, start_time: str, end_time: str) -> dict:
    """
    Check which team members are available during a given time window.

    NOTE: This feature is not yet available. Backend calendar endpoints have
    not been implemented. Returns a structured error response; do not treat
    as a positive availability confirmation.

    Args:
        team_id: Integer team ID.
        start_time: Start of window — ISO 8601, e.g. 2024-11-15T16:00
        end_time: End of window — ISO 8601, e.g. 2024-11-15T17:00

    Returns:
        { "available": false, "available_members": [], "error": "..." }
    """
    return spacepilot_tools.check_team_availability(team_id, start_time, end_time)


@mcp.tool()
def get_events() -> dict:
    """
    Get all upcoming campus events from the backend.

    Use to find out what events are happening on campus.

    Returns:
        { "events": [ { id, name, location, start_time, end_time } ], "total": int }
        or { "error": "..." } if the backend is unavailable.
    """
    return spacepilot_tools.get_events()


@mcp.tool()
def check_policy(query: str = None) -> dict:
    """
    Look up campus workspace policies.

    Use to check rules about booking duration, noise, food, or other policies.
    Optionally filter by a keyword (e.g. "booking", "noise", "food").

    Args:
        query: Optional keyword to filter policies by name or description.

    Returns:
        { "policies": [ { id, name, description } ], "total": int, "query": str }
        or { "error": "..." } on failure.
    """
    return spacepilot_tools.check_policy(query)


@mcp.tool()
def create_booking(
    room_id: int,
    user_id: int,
    start_time: str,
    end_time: str,
    purpose: str = None,
) -> dict:
    """
    Create a new room booking in the backend.

    Always call check_room_availability first to confirm the slot is free.
    Do not call this if availability_checked was false in find_rooms results.

    Args:
        room_id: Room to book (integer ID from find_rooms or get_room_details).
        user_id: ID of the user making the booking (positive integer).
        start_time: ISO 8601 start time, e.g. 2024-11-15T16:00
        end_time: ISO 8601 end time, e.g. 2024-11-15T17:00
        purpose: Optional description of the meeting or event.

    Returns:
        { id, room_id, user_id, start_time, end_time, purpose, status }
        on success (status will be "confirmed"), or { "error": "..." } on failure.
    """
    return spacepilot_tools.create_booking(room_id, user_id, start_time, end_time, purpose)


@mcp.tool()
def update_booking(
    booking_id: int,
    start_time: str = None,
    end_time: str = None,
    purpose: str = None,
) -> dict:
    """
    Update an existing booking's time slot or purpose.

    At least one of start_time, end_time, or purpose must be provided.
    The backend is authoritative — success means the backend confirmed the change.

    Args:
        booking_id: ID of the booking to update (positive integer).
        start_time: New start time — ISO 8601, e.g. 2024-11-15T16:00
        end_time: New end time — ISO 8601, e.g. 2024-11-15T17:00
        purpose: New description for the booking.

    Returns:
        Updated booking { id, room_id, user_id, start_time, end_time, purpose, status }
        or { "error": "..." } on failure.
    """
    return spacepilot_tools.update_booking(booking_id, start_time, end_time, purpose)


@mcp.tool()
def cancel_booking(booking_id: int) -> dict:
    """
    Cancel a booking. Sets its status to 'cancelled' in the backend.

    The backend is authoritative — only report success when it confirms.
    A cancelled booking does not free up the slot in the local cache;
    always re-query availability for subsequent bookings.

    Args:
        booking_id: ID of the booking to cancel (positive integer).

    Returns:
        { id, room_id, user_id, start_time, end_time, purpose, status: "cancelled" }
        or { "error": "..." } if the booking was not found or the backend is unavailable.
    """
    return spacepilot_tools.cancel_booking(booking_id)


@mcp.tool()
def notify_team(team_id: int, message: str) -> dict:
    """
    Send a notification to all members of a team.

    NOTE: This feature is not yet available. No notification service is integrated.
    Returns a structured error response; the message will NOT be delivered.

    Args:
        team_id: Integer team ID.
        message: Message text to send.

    Returns:
        { "sent": false, "error": "..." }
    """
    return spacepilot_tools.notify_team(team_id, message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    print("=" * 55)
    print("  SpacePilot MCP Server")
    print("=" * 55)
    print(f"  Transport : Streamable HTTP (MCP 2025-11-25+)")
    print(f"  Endpoint  : http://{HOST}:{PORT}/mcp")
    print(f"  Backend   : {backend_url}")
    print(f"  Tools     : {len(mcp._tool_manager._tools)} registered")
    print("=" * 55)

    # Streamable HTTP transport — required for Alexa+ and remote MCP clients
    mcp.run(transport="streamable-http")

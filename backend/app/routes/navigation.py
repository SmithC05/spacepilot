from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/route")
def get_route(
    from_room: Optional[str] = None,
    to_room: Optional[str] = None,
    accessible: bool = False,
):
    """
    Get a navigation route between two rooms.

    TODO: Implement real pathfinding with campus map data.
    For now, returns a placeholder response.
    """
    return {
        "from": from_room,
        "to": to_room,
        "accessible": accessible,
        "steps": [
            "Navigate to the main corridor",
            "Turn right at the elevator",
            f"Destination: {to_room}",
        ],
        "note": "Placeholder — real routing not yet implemented.",
    }

"""
backend/app/routes/notifications.py

POST /notifications — log a notification to the database.

Accepts:
  { "message": str, "user_id": int (optional), "team_id": int (optional) }

Returns:
  { "id": int, "user_id": ..., "team_id": ..., "message": ..., "created_at": str }

At least one of user_id or team_id must be present.
No real delivery is performed — this unblocks the notify_team MCP tool stub.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel  # used only for request body; lightweight import
from typing import Optional

router = APIRouter(tags=["notifications"])

_DB_FILE = Path(__file__).resolve().parents[2] / "data" / "spacepilot.db"

# DDL — created once if the table doesn't exist
_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    team_id    INTEGER,
    message    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);
"""


def _ensure_table() -> None:
    con = sqlite3.connect(_DB_FILE)
    con.execute(_CREATE_SQL)
    con.commit()
    con.close()


_ensure_table()


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class NotificationCreate(BaseModel):
    message:  str
    user_id:  Optional[int] = None
    team_id:  Optional[int] = None


# ---------------------------------------------------------------------------
# POST /notifications
# ---------------------------------------------------------------------------

@router.post("/notifications", tags=["notifications"], status_code=201)
def create_notification(payload: NotificationCreate):
    """
    Log a notification. Returns the persisted record with its generated ID.

    Real delivery (email/push/Slack) is not wired — the notify_team MCP stub
    can call this endpoint to produce a concrete, non-error response.
    """
    if payload.user_id is None and payload.team_id is None:
        return JSONResponse(
            status_code=422,
            content={"error": "At least one of user_id or team_id must be provided."},
        )
    if not payload.message.strip():
        return JSONResponse(status_code=422, content={"error": "message must not be empty."})

    created_at = datetime.now(timezone.utc).isoformat()

    try:
        con = sqlite3.connect(_DB_FILE)
        cur = con.execute(
            "INSERT INTO notifications (user_id, team_id, message, created_at) VALUES (?, ?, ?, ?)",
            (payload.user_id, payload.team_id, payload.message.strip(), created_at),
        )
        notif_id = cur.lastrowid
        con.commit()
        con.close()
    except sqlite3.OperationalError as e:
        return JSONResponse(status_code=503, content={"error": f"Database error: {e}"})

    return JSONResponse(
        status_code=201,
        content={
            "id":         notif_id,
            "user_id":    payload.user_id,
            "team_id":    payload.team_id,
            "message":    payload.message.strip(),
            "created_at": created_at,
            "delivered":  False,
            "note":       "Notification logged. Real delivery (email/push) not yet integrated.",
        },
    )


# ---------------------------------------------------------------------------
# GET /notifications  — list recent (useful for debugging)
# ---------------------------------------------------------------------------

@router.get("/notifications", tags=["notifications"])
def list_notifications(limit: int = 20):
    """List the most recent notifications (newest first). For debugging."""
    try:
        con = sqlite3.connect(_DB_FILE)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        con.close()
    except sqlite3.OperationalError as e:
        return JSONResponse(status_code=503, content={"error": f"Database error: {e}"})
    return JSONResponse(content={"notifications": [dict(r) for r in rows], "total": len(rows)})

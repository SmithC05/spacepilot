"""
backend/app/seed.py
===================
Seed (or re-seed) the rooms table from campus spatial and feature data.

Usage (from the backend/ directory — no venv needed, stdlib only):
    python app/seed.py

What it does:
  1. Reads DATA/MAP_NODE/campus_maps.json  — spatial nodes (id, name, x, y)
  2. Reads DATA/MAP_NODE/room_features.json — feature metadata keyed by room_id
  3. Joins on node id (campus_maps node.id == room_features.room_id)
  4. Parses building and floor from the node_id prefix
  5. Upserts into the `rooms` table (keyed by node_id):
       - If node_id not in DB → INSERT
       - If node_id already exists → UPDATE all columns
  6. Prints a summary and 5-row sample for sanity-checking.

Supported node_id prefix patterns
──────────────────────────────────
  "200_node_009"           → building="200",     floor=None
  "300_node_001"           → building="300",     floor=None
  "500_node_001"           → building="500",     floor=None
  "600_node_001"           → building="600",     floor=None
  "blocka0f1_node_001"     → building="blocka",  floor=0
  "blocka1fl_node_009"     → building="blocka",  floor=1
  "blocka3fl_node_005"     → building="blocka",  floor=3
  "blockb0fl_node_001"     → building="blockb",  floor=0
  "blockb1f1_node_001"     → building="blockb",  floor=1
  "blockc2f1_node_001"     → building="blockc",  floor=2
  "cit1fl_node_001"        → building="cit",     floor=1
  "cit2ndf_node_001"       → building="cit",     floor=2
  "cit3f_node_001"         → building="cit",     floor=3
  "citgroundf_node_001"    → building="cit",     floor=0
  "citar_node_001"         → building="cit",     floor=None
  "citcampus_node_xxx"     → building="cit",     floor=None

Requires: Python 3.11+ stdlib only (json, sqlite3, re, pathlib).
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BACKEND_DIR       = Path(__file__).resolve().parent.parent          # backend/
ROOT              = BACKEND_DIR.parent                               # spacepilot/
DATA_DIR          = ROOT / "DATA" / "MAP_NODE"
CAMPUS_MAPS_FILE  = DATA_DIR / "campus_maps.json"
ROOM_FEATURES_FILE = DATA_DIR / "room_features.json"
DB_FILE           = BACKEND_DIR / "data" / "spacepilot.db"


# ---------------------------------------------------------------------------
# Building / floor parser
# ---------------------------------------------------------------------------

def parse_node_prefix(node_id: str) -> tuple[str | None, int | None]:
    """
    Return (building, floor) parsed from the node_id prefix (everything before _node_).
    Prints a WARNING for patterns that can't be confidently parsed.
    """
    if "_node_" not in node_id:
        print(f"  WARNING: '{node_id}' has no '_node_' separator — cannot parse prefix.")
        return None, None

    prefix = node_id.split("_node_")[0]

    # cit* special cases — most-specific first
    if prefix == "citgroundf":
        return "cit", 0
    if prefix in ("citar", "citcampus"):
        return "cit", None
    m = re.match(r"^cit(\d+)(?:ndf|fl?)$", prefix)          # cit1fl, cit2ndf, cit3f
    if m:
        return "cit", int(m.group(1))

    # block<letter><digit>fl / block<letter><digit>f1
    m = re.match(r"^(block[a-z]+?)(\d)(?:fl|f1)$", prefix)
    if m:
        return m.group(1), int(m.group(2))

    # plain numeric block (200, 300, 500, 600) — no floor info in ID
    m = re.match(r"^(\d{3})$", prefix)
    if m:
        return m.group(1), None

    # Known single-location buildings with no floor marker in the node_id
    # building = lowercase prefix for consistency; floor = None
    _KNOWN_SINGLE_FLOOR = {
        "digital_library": "digital_library",
        "library":          "library",
        "Map":              "map",     # capitalised in the raw data → normalise to lowercase
    }
    if prefix in _KNOWN_SINGLE_FLOOR:
        return _KNOWN_SINGLE_FLOOR[prefix], None

    print(f"  WARNING: Cannot confidently parse building/floor from prefix '{prefix}' (node_id='{node_id}')")
    return None, None


# ---------------------------------------------------------------------------
# DDL — ensure rooms table has all required columns
# ---------------------------------------------------------------------------

_CREATE_ROOMS_TABLE = """
CREATE TABLE IF NOT EXISTS rooms (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id              TEXT    UNIQUE,
    name                 TEXT    NOT NULL,
    building             TEXT,
    floor                INTEGER,
    x                    REAL,
    y                    REAL,
    capacity             INTEGER NOT NULL DEFAULT 0,
    projector            INTEGER NOT NULL DEFAULT 0,
    accessible           INTEGER NOT NULL DEFAULT 0,
    ac                   INTEGER NOT NULL DEFAULT 0,
    projector_type       TEXT,
    wifi_quality         TEXT,
    whiteboard           INTEGER NOT NULL DEFAULT 0,
    computers            INTEGER NOT NULL DEFAULT 0,
    noise_level          TEXT,
    booking_restrictions TEXT    NOT NULL DEFAULT 'none'
);
"""

# Column additions for existing DBs that predate this seed script
_ALTER_STATEMENTS = [
    "ALTER TABLE rooms ADD COLUMN node_id TEXT UNIQUE",
    "ALTER TABLE rooms ADD COLUMN x REAL",
    "ALTER TABLE rooms ADD COLUMN y REAL",
    "ALTER TABLE rooms ADD COLUMN ac INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE rooms ADD COLUMN projector_type TEXT",
    "ALTER TABLE rooms ADD COLUMN wifi_quality TEXT",
    "ALTER TABLE rooms ADD COLUMN whiteboard INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE rooms ADD COLUMN computers INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE rooms ADD COLUMN noise_level TEXT",
    "ALTER TABLE rooms ADD COLUMN booking_restrictions TEXT NOT NULL DEFAULT 'none'",
]


def _ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(_CREATE_ROOMS_TABLE)
    # Attempt each ALTER — ignore "duplicate column" errors for idempotency
    for stmt in _ALTER_STATEMENTS:
        try:
            con.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists
    con.commit()


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

_UPSERT_SQL = """
INSERT INTO rooms (
    node_id, name, building, floor, x, y,
    capacity, projector, accessible,
    ac, projector_type, wifi_quality,
    whiteboard, computers, noise_level, booking_restrictions
) VALUES (
    :node_id, :name, :building, :floor, :x, :y,
    :capacity, :projector, :accessible,
    :ac, :projector_type, :wifi_quality,
    :whiteboard, :computers, :noise_level, :booking_restrictions
)
ON CONFLICT(node_id) DO UPDATE SET
    name                 = excluded.name,
    building             = excluded.building,
    floor                = excluded.floor,
    x                    = excluded.x,
    y                    = excluded.y,
    capacity             = excluded.capacity,
    projector            = excluded.projector,
    accessible           = excluded.accessible,
    ac                   = excluded.ac,
    projector_type       = excluded.projector_type,
    wifi_quality         = excluded.wifi_quality,
    whiteboard           = excluded.whiteboard,
    computers            = excluded.computers,
    noise_level          = excluded.noise_level,
    booking_restrictions = excluded.booking_restrictions;
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed() -> None:
    print("=" * 60)
    print("  SpacePilot — Room Seed  (stdlib sqlite3, no venv needed)")
    print("=" * 60)

    # 1. Load spatial nodes
    if not CAMPUS_MAPS_FILE.exists():
        sys.exit(f"ERROR: {CAMPUS_MAPS_FILE} not found.")
    with open(CAMPUS_MAPS_FILE, encoding="utf-8") as f:
        campus_data = json.load(f)

    spatial_rooms: dict[str, dict] = {}
    for map_data in campus_data.get("maps", []):
        for node in map_data.get("nodes", []):
            if node.get("type") == "ROOM":
                spatial_rooms[node["id"]] = {
                    "name": node.get("name", ""),
                    "x":    node.get("x"),
                    "y":    node.get("y"),
                }
    print(f"\n[1/4] Loaded {len(spatial_rooms)} ROOM nodes from campus_maps.json.")

    # 2. Load feature data
    if not ROOM_FEATURES_FILE.exists():
        sys.exit(f"ERROR: {ROOM_FEATURES_FILE} not found. Run generate_features.py first.")
    with open(ROOM_FEATURES_FILE, encoding="utf-8") as f:
        features_by_id: dict[str, dict] = {r["room_id"]: r for r in json.load(f)}
    print(f"[2/4] Loaded {len(features_by_id)} entries from room_features.json.")

    # 3. Ensure DB + schema
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_FILE)
    _ensure_schema(con)
    print(f"[3/4] Schema ready. Upserting into {DB_FILE} ...")

    created = 0
    updated = 0
    skipped_no_feat = 0
    skipped_orphan_feat = 0
    sample_parsed: list[tuple] = []

    rows: list[dict] = []
    for node_id, spatial in spatial_rooms.items():
        feat = features_by_id.get(node_id)
        if feat is None:
            skipped_no_feat += 1
            continue

        building, floor = parse_node_prefix(node_id)
        if len(sample_parsed) < 5:
            sample_parsed.append((node_id, building, floor))

        rows.append({
            "node_id":              node_id,
            "name":                 spatial["name"],
            "building":             building,
            "floor":                floor,
            "x":                    spatial["x"],
            "y":                    spatial["y"],
            "capacity":             feat["capacity"],
            "projector":            int(feat["projector"]),
            "accessible":           int(feat["wheelchair_accessible"]),
            "ac":                   int(feat["ac"]),
            "projector_type":       feat.get("projector_type"),
            "wifi_quality":         feat["wifi_quality"],
            "whiteboard":           int(feat["whiteboard"]),
            "computers":            feat["computers"],
            "noise_level":          feat["noise_level"],
            "booking_restrictions": feat["booking_restrictions"],
        })

    # Check which node_ids already exist to report created vs updated
    existing_ids: set[str] = set()
    for (nid,) in con.execute("SELECT node_id FROM rooms WHERE node_id IS NOT NULL"):
        existing_ids.add(nid)

    for row in rows:
        if row["node_id"] in existing_ids:
            updated += 1
        else:
            created += 1

    con.executemany(_UPSERT_SQL, rows)
    con.commit()

    # Orphan feature entries (in features file but no spatial node)
    for fid in features_by_id:
        if fid not in spatial_rooms:
            print(f"  WARNING: room_features entry '{fid}' has no spatial node — skipped.")
            skipped_orphan_feat += 1

    con.close()

    # 4. Summary
    print("\n[4/4] Seed complete.")
    print(f"  Rooms created : {created}")
    print(f"  Rooms updated : {updated}")
    print(f"  Skipped (no feature data)      : {skipped_no_feat}")
    print(f"  Skipped (orphan feature entry) : {skipped_orphan_feat}")

    print("\n  Sample building/floor parsing (first 5 rooms):")
    print(f"  {'node_id':<38} {'building':<12} floor")
    print(f"  {'-'*38} {'-'*12} -----")
    for nid, bld, flr in sample_parsed:
        print(f"  {nid:<38} {str(bld):<12} {str(flr)}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Static seed: Policies + CampusEvents
# ---------------------------------------------------------------------------

def seed_static_data() -> None:
    """
    Idempotently insert Policy and CampusEvent seed rows.
    Uses INSERT OR IGNORE so re-running is safe.
    """
    print("\n" + "=" * 60)
    print("  SpacePilot — Static Data Seed (Policies + CampusEvents)")
    print("=" * 60)

    con = sqlite3.connect(DB_FILE)

    # ── Ensure tables exist ─────────────────────────────────────────────────
    con.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS campus_events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            location   TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL
        )
    """)
    con.commit()

    # ── Policies ────────────────────────────────────────────────────────────
    policies = [
        (
            "Open Booking",
            "Rooms marked 'none' under booking_restrictions may be booked by any campus "
            "member with no approval required. Bookings must be made at least 30 minutes "
            "in advance and released if unused within 15 minutes of the start time.",
        ),
        (
            "Staff-Only Rooms",
            "Rooms marked 'staff-only' are reserved exclusively for faculty and staff. "
            "Student bookings will be automatically rejected. Examples include HOD offices, "
            "staff rooms, and administrative spaces.",
        ),
        (
            "Maximum 2-Hour Booking",
            "Rooms marked 'max-2hr' enforce a hard cap of 2 hours per booking per user per day. "
            "Back-to-back bookings by the same user for the same room are not permitted. "
            "Extension requests must be submitted to the facilities office.",
        ),
        (
            "Approval-Required Rooms",
            "Rooms marked 'approval-required' — including seminar halls, large lecture theatres, "
            "and computer centres — require written approval from the department head or "
            "facilities coordinator. Submit requests at least 48 hours in advance.",
        ),
        (
            "Noise & Conduct Policy",
            "All bookable spaces are subject to campus noise standards. Quiet zones (rooms "
            "with noise_level='quiet') must be maintained at library-level noise. Booking a "
            "room does not grant permission to disturb adjacent spaces.",
        ),
        (
            "Cancellation Policy",
            "Bookings may be cancelled up to 1 hour before the start time at no penalty. "
            "Late cancellations (< 1 hour) or no-shows are recorded and may result in "
            "temporary booking restrictions being applied to the user's account.",
        ),
    ]

    p_created = 0
    p_skipped = 0
    for name, description in policies:
        cur = con.execute(
            "INSERT OR IGNORE INTO policies (name, description) VALUES (?, ?)",
            (name, description),
        )
        if cur.rowcount:
            p_created += 1
        else:
            p_skipped += 1
    con.commit()

    # ── CampusEvents ────────────────────────────────────────────────────────
    # Locations are real room names from the seeded rooms table where possible.
    campus_events = [
        (
            "Annual Hackathon Kickoff 2026",
            "Seminar hall 1",           # cit1fl — large seminar hall
            "2026-09-20 09:00:00",
            "2026-09-20 18:00:00",
        ),
        (
            "CSE Department Induction",
            "F6 / CSE Staffroom 2",     # cit1fl — CSE staff room
            "2026-09-15 10:00:00",
            "2026-09-15 12:00:00",
        ),
        (
            "Campus Placement Drive — TCS",
            "CDC / Placement cell",     # cit1fl — placement cell
            "2026-09-25 08:30:00",
            "2026-09-25 17:00:00",
        ),
        (
            "Cloud & Security Lab Workshop",
            "Cloud and Security lab",   # cit1fl
            "2026-10-02 14:00:00",
            "2026-10-02 17:00:00",
        ),
        (
            "Inter-Block Sports Day",
            "Digital Library / 403",    # digital_library
            "2026-10-10 08:00:00",
            "2026-10-10 20:00:00",
        ),
    ]

    e_created = 0
    e_skipped = 0
    for name, location, start_time, end_time in campus_events:
        cur = con.execute(
            "INSERT OR IGNORE INTO campus_events (name, location, start_time, end_time) "
            "VALUES (?, ?, ?, ?)",
            (name, location, start_time, end_time),
        )
        if cur.rowcount:
            e_created += 1
        else:
            e_skipped += 1
    con.commit()
    con.close()

    print(f"\n  Policies  — created: {p_created}, already existed: {p_skipped}")
    print(f"  Events    — created: {e_created}, already existed: {e_skipped}")
    print("=" * 60)



# ---------------------------------------------------------------------------
# Static seed: Teams + Users + CalendarEvents
# ---------------------------------------------------------------------------

def seed_people_data() -> None:
    """
    Idempotently insert Team, User, and CalendarEvent seed rows.
    """
    print("\n" + "=" * 60)
    print("  SpacePilot — People Data Seed (Teams, Users, Calendar)")
    print("=" * 60)

    con = sqlite3.connect(DB_FILE)

    # ── Ensure tables exist (with unique constraints where needed) ──────────
    con.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            team_id INTEGER,
            FOREIGN KEY(team_id) REFERENCES teams(id)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    con.commit()

    # ── Teams ───────────────────────────────────────────────────────────────
    teams_data = [
        "Backend Infrastructure",
        "Frontend Engineering",
        "Product Management",
        "Campus Operations"
    ]

    t_created = 0
    t_skipped = 0
    for t_name in teams_data:
        cur = con.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (t_name,))
        if cur.rowcount:
            t_created += 1
        else:
            t_skipped += 1
    
    t_rows = con.execute("SELECT id, name FROM teams").fetchall()
    team_map = {row[1]: row[0] for row in t_rows}

    # ── Users ───────────────────────────────────────────────────────────────
    users_data = [
        ("Alice Chen", "alice.chen@spacepilot.local", "Backend Infrastructure"),
        ("Bob Smith", "bob.smith@spacepilot.local", "Backend Infrastructure"),
        ("Charlie Davis", "charlie.d@spacepilot.local", "Backend Infrastructure"),
        ("Diana Prince", "diana.p@spacepilot.local", "Frontend Engineering"),
        ("Evan Wright", "evan.w@spacepilot.local", "Frontend Engineering"),
        ("Fiona Gallagher", "fiona.g@spacepilot.local", "Frontend Engineering"),
        ("George Costanza", "george.c@spacepilot.local", "Product Management"),
        ("Hannah Abbott", "hannah.a@spacepilot.local", "Product Management"),
        ("Ian Malcolm", "ian.m@spacepilot.local", "Product Management"),
        ("Jane Doe", "jane.doe@spacepilot.local", "Campus Operations"),
        ("Kevin Malone", "kevin.m@spacepilot.local", "Campus Operations"),
        ("Laura Palmer", "laura.p@spacepilot.local", "Campus Operations"),
    ]

    u_created = 0
    u_skipped = 0
    for u_name, u_email, t_name in users_data:
        t_id = team_map[t_name]
        cur = con.execute(
            "INSERT OR IGNORE INTO users (name, email, team_id) VALUES (?, ?, ?)", 
            (u_name, u_email, t_id)
        )
        if cur.rowcount:
            u_created += 1
        else:
            u_skipped += 1

    u_rows = con.execute("SELECT id, email FROM users").fetchall()
    user_map = {row[1]: row[0] for row in u_rows}

    # ── CalendarEvents ──────────────────────────────────────────────────────
    # Target date: 2026-09-16.
    # Backend Infrastructure will have conflicts between 10:00 and 11:00:
    # Alice: 09:30 - 10:30 (overlaps 10:00 - 11:00)
    # Bob:   10:45 - 11:30 (overlaps 10:00 - 11:00)
    # Charlie: 14:00 - 15:00 (free 10:00 - 11:00)
    
    events_data = [
        # Backend Infrastructure
        ("alice.chen@spacepilot.local", "DB Migration sync", "2026-09-16 09:30:00", "2026-09-16 10:30:00"),
        ("alice.chen@spacepilot.local", "1:1 with Manager", "2026-09-16 13:00:00", "2026-09-16 13:30:00"),
        ("bob.smith@spacepilot.local", "API Design Review", "2026-09-16 10:45:00", "2026-09-16 11:30:00"),
        ("charlie.d@spacepilot.local", "Heads down coding", "2026-09-16 14:00:00", "2026-09-16 15:00:00"),
        
        # Frontend Engineering (completely free from 10:00 - 11:00)
        ("diana.p@spacepilot.local", "UI Review", "2026-09-16 11:00:00", "2026-09-16 12:00:00"),
        ("evan.w@spacepilot.local", "Component testing", "2026-09-16 14:00:00", "2026-09-16 16:00:00"),
        ("fiona.g@spacepilot.local", "Design handoff", "2026-09-16 16:30:00", "2026-09-16 17:30:00"),
        
        # Product Management
        ("george.c@spacepilot.local", "Roadmap planning", "2026-09-16 09:00:00", "2026-09-16 12:00:00"),
        ("hannah.a@spacepilot.local", "Customer calls", "2026-09-16 13:00:00", "2026-09-16 17:00:00"),
        ("ian.m@spacepilot.local", "Metrics review", "2026-09-16 10:30:00", "2026-09-16 11:00:00"),
        
        # Campus Operations
        ("jane.doe@spacepilot.local", "Vendor meeting", "2026-09-16 09:00:00", "2026-09-16 10:00:00"),
        ("kevin.m@spacepilot.local", "Site walk", "2026-09-16 11:00:00", "2026-09-16 12:00:00"),
        ("laura.p@spacepilot.local", "Budget review", "2026-09-16 15:00:00", "2026-09-16 16:00:00"),
    ]

    c_created = 0
    c_skipped = 0
    for u_email, title, start_time, end_time in events_data:
        u_id = user_map[u_email]
        existing = con.execute(
            "SELECT id FROM calendar_events WHERE user_id=? AND title=? AND start_time=? AND end_time=?", 
            (u_id, title, start_time, end_time)
        ).fetchone()
        
        if not existing:
            con.execute(
                "INSERT INTO calendar_events (user_id, title, start_time, end_time) VALUES (?, ?, ?, ?)", 
                (u_id, title, start_time, end_time)
            )
            c_created += 1
        else:
            c_skipped += 1
            
    con.commit()
    con.close()
    print(f"\n  Teams     — created: {t_created}, already existed: {t_skipped}")
    print(f"  Users     — created: {u_created}, already existed: {u_skipped}")
    print(f"  Events    — created: {c_created}, already existed: {c_skipped}")
    print("=" * 60)


if __name__ == "__main__":
    seed()
    seed_static_data()
    seed_people_data()

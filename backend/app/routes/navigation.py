"""
backend/app/routes/navigation.py

Real Dijkstra-based campus navigation — backend-owned implementation.

Endpoints:
  GET /routes?from_id=X&to_id=Y              — shortest path
  GET /routes/accessible?from_id=X&to_id=Y  — same shortest path, but
     flags stair-nodes in the route and warns if stairs are unavoidable.
     NOTE: campus_maps.json has no explicit edge-level accessibility field
     (no "accessible": false on edges). Stair detection relies on node names
     containing "stair". True stair-avoiding routing will require edge metadata
     to be added to campus_maps.json in a future iteration.

Also retains the legacy /navigation/route placeholder endpoint so existing
calls don't break — it now delegates to the real Dijkstra implementation.

Data: DATA/MAP_NODE/campus_maps.json (read at import time, cached in module scope).
"""

import heapq
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(tags=["navigation"])

# ---------------------------------------------------------------------------
# Load + build graph (module-level, cached)
# ---------------------------------------------------------------------------

_DATA_FILE = Path(__file__).resolve().parents[3] / "DATA" / "MAP_NODE" / "campus_maps.json"


def _normalize_node_id(node_id: str, map_id: str) -> str:
    """Fix the '500' map edge bug where edges say 'Map_node_xxx' but nodes are '500_node_xxx'."""
    if node_id.startswith("Map_node_"):
        return f"{map_id}_node_{node_id[len('Map_node_'):]}"
    return node_id


def _build_graph(campus_data: dict):
    """
    Returns:
        graph      : {node_id: [(neighbor_id, weight), ...]}
        nodes      : {node_id: {id, name, type, category, x, y, map_id, map_name, level}}
        room_index : {lowercase_name: [node_id, ...]}
    """
    graph: dict[str, list[tuple[str, float]]] = {}
    nodes: dict[str, dict] = {}
    room_index: dict[str, list[str]] = {}

    for campus_map in campus_data.get("maps", []):
        map_id   = campus_map["id"]
        map_name = campus_map.get("name", map_id)
        level    = campus_map.get("level", 0)

        for node in campus_map.get("nodes", []):
            nid = node["id"]
            nodes[nid] = {**node, "map_id": map_id, "map_name": map_name, "level": level}
            if node.get("type") == "ROOM":
                key = node["name"].strip().lower()
                room_index.setdefault(key, []).append(nid)

        for edge in campus_map.get("edges", []):
            src = _normalize_node_id(edge["source"], map_id)
            tgt = _normalize_node_id(edge["target"], map_id)
            w   = float(edge.get("weight", 1))
            bi  = edge.get("bidirectional", True)
            graph.setdefault(src, []).append((tgt, w))
            if bi:
                graph.setdefault(tgt, []).append((src, w))

    return graph, nodes, room_index


try:
    with open(_DATA_FILE, encoding="utf-8") as _f:
        _CAMPUS_DATA = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError):
    _CAMPUS_DATA = {"maps": []}

_GRAPH, _NODES, _ROOM_INDEX = _build_graph(_CAMPUS_DATA)


# ---------------------------------------------------------------------------
# Dijkstra
# ---------------------------------------------------------------------------

def _dijkstra(start: str, end: str) -> tuple[Optional[list[str]], Optional[float]]:
    if start not in _NODES and start not in _GRAPH:
        return None, None
    dist: dict[str, float] = {start: 0.0}
    prev: dict[str, str] = {}
    heap = [(0.0, start)]
    visited: set[str] = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == end:
            break
        for v, w in _GRAPH.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if end not in dist:
        return None, None
    path: list[str] = []
    cur = end
    while cur in prev:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    path.reverse()
    return path, dist[end]


# ---------------------------------------------------------------------------
# Path → steps
# ---------------------------------------------------------------------------

def _path_to_steps(path: list[str]) -> list[dict]:
    steps = []
    step_num = 1
    for i, nid in enumerate(path):
        node = _NODES.get(nid, {})
        name = node.get("name", nid)
        is_endpoint = (i == 0 or i == len(path) - 1)
        is_named    = not re.match(r"^node \d+$", name.lower())
        if not is_named and not is_endpoint:
            continue
        node_type = node.get("type", "NORMAL")
        if node_type == "GATEWAY":
            nl = name.lower()
            if "stair" in nl:
                instruction = f"Take stairs: {name}"
            elif any(w in nl for w in ("entrance", "exit", "gate", "side")):
                instruction = f"Pass through {name}"
            else:
                instruction = f"Go to {name}"
        elif node_type == "ROOM":
            if i == len(path) - 1:
                instruction = f"Arrive at {name}"
            elif i == 0:
                instruction = f"Start at {name}"
            else:
                instruction = f"Pass {name}"
        else:
            if i == 0:
                instruction = f"Start at {name}"
            elif is_named:
                instruction = f"Continue to {name}"
            else:
                continue
        steps.append({"step": step_num, "instruction": instruction, "node_id": nid})
        step_num += 1
    return steps


# ---------------------------------------------------------------------------
# Core route builder
# ---------------------------------------------------------------------------

def _find_node(room_or_node_id: str) -> Optional[str]:
    """Resolve a room name or node_id string to a graph node ID."""
    # Exact node_id match
    if room_or_node_id in _NODES:
        return room_or_node_id
    # Case-insensitive room name lookup
    key = room_or_node_id.strip().lower()
    if key in _ROOM_INDEX:
        return _ROOM_INDEX[key][0]
    # Substring match fallback
    for indexed_name, node_ids in _ROOM_INDEX.items():
        if key in indexed_name or indexed_name in key:
            return node_ids[0]
    return None


def _build_route_response(from_id: str, to_id: str, accessible: bool) -> dict:
    from_node = _find_node(from_id)
    to_node   = _find_node(to_id)

    if from_node is None:
        return {"error": f"Room/node '{from_id}' not found in campus map."}
    if to_node is None:
        return {"error": f"Room/node '{to_id}' not found in campus map."}
    if from_node == to_node:
        return {
            "from_id": from_id, "to_id": to_id, "accessible": accessible,
            "steps": [{"step": 1, "instruction": f"You are already at {from_id}.", "node_id": from_node}],
            "distance_units": 0, "has_stairs": False,
        }

    from_info = _NODES[from_node]
    to_info   = _NODES[to_node]

    if from_info["map_id"] != to_info["map_id"]:
        return {
            "from_id": from_id, "to_id": to_id, "accessible": accessible,
            "cross_building": True,
            "from_location": from_info["map_name"],
            "to_location":   to_info["map_name"],
            "steps": [
                {"step": 1, "instruction": f"Start at {from_id} in {from_info['map_name']}"},
                {"step": 2, "instruction": "Exit the building and follow the main campus path"},
                {"step": 3, "instruction": f"Enter {to_info['map_name']}"},
                {"step": 4, "instruction": f"Arrive at {to_id}"},
            ],
            "note": (
                "Cross-building routing uses a simplified path. "
                "Full multi-building pathfinding requires edge metadata linking gateway nodes "
                "across maps — not yet present in campus_maps.json."
            ),
        }

    path, distance = _dijkstra(from_node, to_node)
    if path is None:
        return {"error": f"No path found between '{from_id}' and '{to_id}'. They may be on disconnected floor sections."}

    has_stairs = any("stair" in _NODES.get(nid, {}).get("name", "").lower() for nid in path)
    steps = _path_to_steps(path)

    result: dict = {
        "from_id":        from_id,
        "to_id":          to_id,
        "accessible":     accessible,
        "map":            from_info["map_name"],
        "steps":          steps,
        "distance_units": round(distance, 1),
        "has_stairs":     has_stairs,
    }

    if accessible and has_stairs:
        result["accessibility_warning"] = (
            "This route includes stairs. campus_maps.json has no edge-level "
            "accessibility metadata, so stair-avoiding routing is not yet possible. "
            "Verify accessibility on-site or contact campus facilities."
        )

    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/routes", tags=["navigation"])
def get_route(
    from_id: str = Query(..., description="Starting room name or node_id (e.g. '201', 'blocka1fl_node_009')"),
    to_id:   str = Query(..., description="Destination room name or node_id"),
):
    """Shortest walking path between two campus rooms/nodes (Dijkstra)."""
    result = _build_route_response(from_id, to_id, accessible=False)
    status = 404 if "error" in result else 200
    return JSONResponse(status_code=status, content=result)


@router.get("/routes/accessible", tags=["navigation"])
def get_accessible_route(
    from_id: str = Query(..., description="Starting room name or node_id"),
    to_id:   str = Query(..., description="Destination room name or node_id"),
):
    """
    Shortest path with accessibility flagging.

    NOTE: campus_maps.json contains no edge-level accessibility field
    (no 'accessible: false' on stair edges). Stair detection is name-based only.
    True stair-avoiding routing requires edge metadata additions to campus_maps.json.
    """
    result = _build_route_response(from_id, to_id, accessible=True)
    status = 404 if "error" in result else 200
    return JSONResponse(status_code=status, content=result)


# ---------------------------------------------------------------------------
# Legacy /navigation/route — delegates to real Dijkstra so existing calls work
# ---------------------------------------------------------------------------

@router.get("/navigation/route", tags=["navigation"])
def get_navigation_route_legacy(
    from_room:  Optional[str] = None,
    to_room:    Optional[str] = None,
    accessible: bool = False,
):
    """Legacy endpoint — delegates to real Dijkstra. Prefer /routes?from_id=&to_id=."""
    if not from_room or not to_room:
        return JSONResponse(
            status_code=422,
            content={"error": "Both from_room and to_room are required."},
        )
    result = _build_route_response(from_room, to_room, accessible=accessible)
    status = 404 if "error" in result else 200
    return JSONResponse(status_code=status, content=result)

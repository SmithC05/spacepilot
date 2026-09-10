"""
Campus navigation using FindMyCampus spatial data.

Loads campus_maps.json and provides Dijkstra-based shortest-path routing.
Returns step-by-step walking directions with distance estimates.

Architecture note:
  This module loads the spatial graph directly from DATA/MAP_NODE/campus_maps.json
  because the backend navigation endpoint is a placeholder (returns hardcoded strings).
  When the backend team implements real pathfinding, update get_route and
  get_accessible_route in tools.py to call GET /navigation/route instead.

Known data issue:
  The '500' map in campus_maps.json has a bug where its edges reference
  'Map_node_xxx' instead of '500_node_xxx'. This module auto-corrects it.
"""

import heapq
import json
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

_DATA_FILE = Path(__file__).parent.parent / "DATA" / "MAP_NODE" / "campus_maps.json"


def _load_campus_data() -> dict:
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


try:
    _CAMPUS_DATA = _load_campus_data()
except FileNotFoundError:
    _CAMPUS_DATA = {"maps": []}
except json.JSONDecodeError as e:
    _CAMPUS_DATA = {"maps": []}


# --------------------------------------------------------------------------
# Graph building
# --------------------------------------------------------------------------

def _normalize_node_id(node_id: str, map_id: str) -> str:
    """
    Fix the edge node-ID bug in the '500' map.
    That map's edges say 'Map_node_001' but nodes are named '500_node_001'.
    """
    if node_id.startswith("Map_node_"):
        suffix = node_id[len("Map_node_"):]
        return f"{map_id}_node_{suffix}"
    return node_id


def _build_graph(campus_data: dict):
    """
    Build adjacency list, node registry, and room name index from campus data.

    Returns:
        graph       : {node_id: [(neighbor_id, weight), ...]}
        nodes       : {node_id: node_dict_with_map_context}
        room_index  : {lowercase_room_name: [node_id, ...]}
    """
    graph: dict[str, list[tuple[str, float]]] = {}
    nodes: dict[str, dict] = {}
    room_index: dict[str, list[str]] = {}

    for campus_map in campus_data.get("maps", []):
        map_id   = campus_map["id"]
        map_name = campus_map.get("name", map_id)
        level    = campus_map.get("level", 0)

        # Index nodes
        for node in campus_map.get("nodes", []):
            nid = node["id"]
            nodes[nid] = {
                **node,
                "map_id":   map_id,
                "map_name": map_name,
                "level":    level,
            }
            if node.get("type") == "ROOM":
                key = node["name"].strip().lower()
                room_index.setdefault(key, []).append(nid)

        # Build adjacency list
        for edge in campus_map.get("edges", []):
            src = _normalize_node_id(edge["source"], map_id)
            tgt = _normalize_node_id(edge["target"], map_id)
            w   = float(edge.get("weight", 1))
            bi  = edge.get("bidirectional", True)

            graph.setdefault(src, []).append((tgt, w))
            if bi:
                graph.setdefault(tgt, []).append((src, w))

    return graph, nodes, room_index


_GRAPH, _NODES, _ROOM_INDEX = _build_graph(_CAMPUS_DATA)


# --------------------------------------------------------------------------
# Room lookup
# --------------------------------------------------------------------------

def find_node_by_room_name(room_name: str) -> Optional[str]:
    """
    Return the first node ID whose room name matches (case-insensitive).
    Falls back to a partial-match scan if an exact match is not found.
    Returns None if the room cannot be found in any map.
    """
    key = room_name.strip().lower()

    # Exact match
    if key in _ROOM_INDEX:
        return _ROOM_INDEX[key][0]

    # Prefix / substring match
    for indexed_name, node_ids in _ROOM_INDEX.items():
        if key in indexed_name or indexed_name in key:
            return node_ids[0]

    return None


def list_all_rooms() -> list[dict]:
    """Return a flat list of all ROOM nodes with map context (useful for debugging)."""
    return [
        {
            "node_id":  nid,
            "name":     n["name"],
            "map_id":   n["map_id"],
            "map_name": n["map_name"],
            "level":    n["level"],
            "x": n.get("x"),
            "y": n.get("y"),
        }
        for nid, n in _NODES.items()
        if n.get("type") == "ROOM"
    ]


# --------------------------------------------------------------------------
# Dijkstra shortest path
# --------------------------------------------------------------------------

def _dijkstra(start: str, end: str) -> tuple[Optional[list[str]], Optional[float]]:
    """
    Dijkstra's algorithm on the campus graph.

    Returns (path_as_node_id_list, total_distance) or (None, None) if
    no path exists between start and end.
    """
    if start not in _NODES and start not in _GRAPH:
        return None, None

    dist: dict[str, float] = {start: 0.0}
    prev: dict[str, str]   = {}
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

    # Reconstruct path
    path: list[str] = []
    cur = end
    while cur in prev:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    path.reverse()

    return path, dist[end]


# --------------------------------------------------------------------------
# Path → human-readable steps
# --------------------------------------------------------------------------

def _path_to_steps(path: list[str]) -> list[dict]:
    """Convert a node-ID path into a list of navigation instruction dicts."""
    steps = []
    step_num = 1

    for i, nid in enumerate(path):
        node = _NODES.get(nid, {})
        name  = node.get("name", nid)

        # Skip anonymous corridor waypoints (named "Node N") unless they
        # are the start or end of the path.
        is_endpoint = (i == 0 or i == len(path) - 1)
        is_named    = not name.lower().startswith("node ")

        if not is_named and not is_endpoint:
            continue

        node_type = node.get("type", "NORMAL")
        if node_type == "GATEWAY":
            name_lower = name.lower()
            if "stair" in name_lower:
                instruction = f"Take stairs: {name}"
            elif any(w in name_lower for w in ("entrance", "exit", "gate", "side")):
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

        steps.append({
            "step":        step_num,
            "instruction": instruction,
            "node_id":     nid,
        })
        step_num += 1

    return steps


# --------------------------------------------------------------------------
# Public routing interface
# --------------------------------------------------------------------------

def get_route_between(from_room: str, to_room: str, accessible: bool = False) -> dict:
    """
    Find a walking route between two campus rooms.

    Args:
        from_room : Room name as it appears on the campus map (e.g. "201", "A101").
        to_room   : Destination room name.
        accessible: If True, the response flags stair-containing routes and
                    warns if no accessible alternative is available.

    Returns a dict that always contains:
        from_room, to_room, accessible
    And on success:
        steps, distance_units, map, has_stairs
    Or on error:
        error (str)
    """
    from_node = find_node_by_room_name(from_room)
    to_node   = find_node_by_room_name(to_room)

    if from_node is None:
        return {
            "error": (
                f"Room '{from_room}' not found in the campus map. "
                "Use the exact room number as it appears on signage (e.g. '201', 'A101', 'F4')."
            )
        }
    if to_node is None:
        return {
            "error": (
                f"Room '{to_room}' not found in the campus map. "
                "Use the exact room number as it appears on signage."
            )
        }

    if from_node == to_node:
        return {
            "from_room":      from_room,
            "to_room":        to_room,
            "accessible":     accessible,
            "steps":          [{"step": 1, "instruction": f"You are already at {from_room}.", "node_id": from_node}],
            "distance_units": 0,
            "has_stairs":     False,
        }

    from_info = _NODES[from_node]
    to_info   = _NODES[to_node]

    # Different maps — cross-building navigation not yet implemented
    if from_info["map_id"] != to_info["map_id"]:
        return {
            "from_room":          from_room,
            "to_room":            to_room,
            "accessible":         accessible,
            "from_location":      from_info["map_name"],
            "to_location":        to_info["map_name"],
            "cross_building":     True,
            "steps": [
                {"step": 1, "instruction": f"Start at {from_room} in {from_info['map_name']}"},
                {"step": 2, "instruction": "Exit the building and navigate to the main campus path"},
                {"step": 3, "instruction": f"Enter {to_info['map_name']}"},
                {"step": 4, "instruction": f"Arrive at {to_room}"},
            ],
            "note": (
                "Cross-building routing uses a simplified path. "
                "Full multi-building pathfinding will be added when the backend "
                "navigation endpoint is implemented."
            ),
        }

    # Same-map Dijkstra
    path, distance = _dijkstra(from_node, to_node)

    if path is None:
        return {
            "error": (
                f"No path found between '{from_room}' and '{to_room}'. "
                "They may be on separate floor sections without a connecting route."
            )
        }

    # Detect stairs in path
    has_stairs = any(
        "stair" in _NODES.get(nid, {}).get("name", "").lower()
        for nid in path
    )

    steps = _path_to_steps(path)

    result = {
        "from_room":      from_room,
        "to_room":        to_room,
        "accessible":     accessible,
        "map":            from_info["map_name"],
        "steps":          steps,
        "distance_units": round(distance, 1),
        "has_stairs":     has_stairs,
    }

    if accessible and has_stairs:
        result["accessibility_warning"] = (
            "This route includes stairs. No lift or elevator data is available for this area. "
            "Please verify accessibility on-site or contact campus facilities."
        )

    return result

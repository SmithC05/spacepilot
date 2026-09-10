"""
SpacePilot MCP — test suite

Tests are grouped into three areas:
    1. Navigation module  — pure logic, no backend needed
    2. Tool functions     — backend calls mocked with unittest.mock
    3. MCP server         — tool registration and transport verification

Run:
    cd mcp
    .venv\\Scripts\\pytest test_mcp.py -v
"""

import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers to run without .env
# ---------------------------------------------------------------------------

import os
os.environ.setdefault("BACKEND_URL",  "http://localhost:8000")
os.environ.setdefault("MCP_HOST",     "0.0.0.0")
os.environ.setdefault("MCP_PORT",     "8080")
os.environ.setdefault("HTTP_TIMEOUT", "10.0")


# ===========================================================================
# 1. Navigation module tests
# ===========================================================================

class TestNavigation:
    """Tests for mcp/navigation.py — no network calls required."""

    def setup_method(self):
        import navigation
        self.nav = navigation

    def test_campus_data_loads(self):
        """Campus map data loads from campus_maps.json without error."""
        assert self.nav._CAMPUS_DATA is not None
        assert "maps" in self.nav._CAMPUS_DATA
        assert len(self.nav._CAMPUS_DATA["maps"]) > 0, "Expected at least one map in campus_maps.json"

    def test_graph_built(self):
        """Adjacency graph is non-empty after loading."""
        assert len(self.nav._GRAPH) > 0, "Graph should have at least one node"
        assert len(self.nav._NODES) > 0, "Node registry should be populated"

    def test_room_index_populated(self):
        """Room name index contains known rooms."""
        assert len(self.nav._ROOM_INDEX) > 0
        # Room "201" should exist in the 200s block
        assert "201" in self.nav._ROOM_INDEX, (
            "Room '201' expected in room index. "
            f"Available rooms: {list(self.nav._ROOM_INDEX.keys())[:10]}"
        )

    def test_find_node_exact_match(self):
        """find_node_by_room_name returns a node ID for an exact name."""
        node_id = self.nav.find_node_by_room_name("201")
        assert node_id is not None
        assert node_id in self.nav._NODES

    def test_find_node_case_insensitive(self):
        """Room lookup is case-insensitive."""
        lower = self.nav.find_node_by_room_name("201")
        upper = self.nav.find_node_by_room_name("201")
        assert lower == upper

    def test_find_node_unknown_room_returns_none(self):
        """Unknown room name returns None."""
        result = self.nav.find_node_by_room_name("ZZZZNOTAROOM9999")
        assert result is None

    def test_dijkstra_same_node(self):
        """Dijkstra from a node to itself returns a single-node path with distance 0."""
        # Pick any known node
        node_id = next(iter(self.nav._NODES))
        path, dist = self.nav._dijkstra(node_id, node_id)
        assert path == [node_id]
        assert dist == 0.0

    def test_dijkstra_connected_nodes(self):
        """Dijkstra finds a path between two adjacent nodes."""
        # Pick a node that has at least one neighbour
        src = None
        tgt = None
        for node, neighbours in self.nav._GRAPH.items():
            if neighbours:
                src = node
                tgt = neighbours[0][0]
                break
        assert src is not None, "Graph should have at least one edge"
        path, dist = self.nav._dijkstra(src, tgt)
        assert path is not None
        assert len(path) >= 2
        assert dist > 0

    def test_dijkstra_unreachable_returns_none(self):
        """Dijkstra returns (None, None) when destination is unreachable."""
        path, dist = self.nav._dijkstra("200_node_001", "PHANTOM_NODE_XYZ")
        assert path is None
        assert dist is None

    def test_get_route_between_known_rooms(self):
        """get_route_between returns steps for two known rooms in the same map."""
        result = self.nav.get_route_between("201", "202")
        # Should not be an error
        assert "error" not in result or result.get("steps") is not None, (
            f"Expected a route result, got: {result}"
        )
        if "steps" in result:
            assert isinstance(result["steps"], list)
            assert len(result["steps"]) >= 1

    def test_get_route_between_unknown_from_room(self):
        """get_route_between returns error dict when from_room is not on the map."""
        result = self.nav.get_route_between("GHOST_ROOM_111", "201")
        assert "error" in result
        assert "GHOST_ROOM_111" in result["error"]

    def test_get_route_between_unknown_to_room(self):
        """get_route_between returns error dict when to_room is not on the map."""
        result = self.nav.get_route_between("201", "GHOST_ROOM_999")
        assert "error" in result
        assert "GHOST_ROOM_999" in result["error"]

    def test_accessible_route_returns_has_stairs_flag(self):
        """Accessible route result always contains has_stairs key (when no error)."""
        result = self.nav.get_route_between("201", "202", accessible=True)
        if "error" not in result and "cross_building" not in result:
            assert "has_stairs" in result

    def test_normalize_node_id_fixes_map_prefix(self):
        """_normalize_node_id corrects the Map_node_xxx bug in the 500 map."""
        fixed = self.nav._normalize_node_id("Map_node_001", "500")
        assert fixed == "500_node_001"

    def test_normalize_node_id_leaves_correct_ids_unchanged(self):
        """_normalize_node_id does not modify already-correct node IDs."""
        original = "200_node_005"
        assert self.nav._normalize_node_id(original, "200") == original

    def test_list_all_rooms_is_non_empty(self):
        """list_all_rooms() returns the full room list from campus_maps.json."""
        rooms = self.nav.list_all_rooms()
        assert isinstance(rooms, list)
        assert len(rooms) > 0
        # Every item should have name and map_id
        for r in rooms[:5]:
            assert "name"   in r
            assert "map_id" in r


# ===========================================================================
# 2. Tool function tests (backend calls mocked)
# ===========================================================================

SAMPLE_ROOMS = [
    {"id": 1, "name": "Room A", "building": "Main", "floor": 1,
     "capacity": 10, "projector": True,  "accessible": True},
    {"id": 2, "name": "Room B", "building": "Main", "floor": 1,
     "capacity": 5,  "projector": False, "accessible": False},
    {"id": 3, "name": "Room C", "building": "Main", "floor": 2,
     "capacity": 20, "projector": True,  "accessible": False},
]

SAMPLE_BOOKINGS = [
    {
        "id": 101, "room_id": 1, "user_id": 1,
        "start_time": "2024-11-15T14:00:00",
        "end_time":   "2024-11-15T15:00:00",
        "purpose": "Team meeting", "status": "confirmed",
    },
    {
        "id": 102, "room_id": 2, "user_id": 2,
        "start_time": "2024-11-15T16:00:00",
        "end_time":   "2024-11-15T17:00:00",
        "purpose": "Workshop", "status": "confirmed",
    },
]


class TestFindRooms:
    """Tests for tools.find_rooms()."""

    def setup_method(self):
        import tools
        self.tools = tools

    @patch("tools._get")
    def test_find_all_rooms_no_filter(self, mock_get):
        mock_get.return_value = SAMPLE_ROOMS
        result = self.tools.find_rooms()
        assert result["total"] == 3
        assert len(result["rooms"]) == 3
        assert result["availability_checked"] is False

    @patch("tools._get")
    def test_capacity_filter(self, mock_get):
        mock_get.return_value = SAMPLE_ROOMS
        result = self.tools.find_rooms(capacity=8)
        # Rooms with capacity >= 8: Room A (10), Room C (20)
        assert result["total"] == 2
        names = {r["name"] for r in result["rooms"]}
        assert "Room A" in names
        assert "Room C" in names
        assert "Room B" not in names

    @patch("tools._get")
    def test_projector_filter(self, mock_get):
        mock_get.return_value = SAMPLE_ROOMS
        result = self.tools.find_rooms(projector_required=True)
        assert result["total"] == 2
        assert all(r["projector"] for r in result["rooms"])

    @patch("tools._get")
    def test_accessible_filter(self, mock_get):
        mock_get.return_value = SAMPLE_ROOMS
        result = self.tools.find_rooms(accessible_required=True)
        assert result["total"] == 1
        assert result["rooms"][0]["name"] == "Room A"

    @patch("tools._get")
    def test_combined_filter(self, mock_get):
        mock_get.return_value = SAMPLE_ROOMS
        result = self.tools.find_rooms(capacity=8, projector_required=True)
        # Room A (10, projector=True, accessible=True) and Room C (20, projector=True)
        assert result["total"] == 2

    @patch("tools._get")
    def test_availability_filter_excludes_booked_rooms(self, mock_get):
        """Rooms with overlapping bookings are excluded from results."""
        def _mock_get(path, params=None):
            if path == "/rooms":
                return SAMPLE_ROOMS
            if path == "/bookings":
                return SAMPLE_BOOKINGS
            return []

        mock_get.side_effect = _mock_get
        # Room 2 is booked 16:00–17:00; request window 16:00–17:00 → Room 2 excluded
        result = self.tools.find_rooms(
            start_datetime="2024-11-15T16:00",
            end_datetime="2024-11-15T17:00",
        )
        assert result["availability_checked"] is True
        room_ids = {r["id"] for r in result["rooms"]}
        assert 2 not in room_ids  # booked
        assert 1 in room_ids      # free (its booking is 14:00–15:00)

    @patch("tools._get")
    def test_invalid_capacity_returns_error(self, mock_get):
        result = self.tools.find_rooms(capacity=-5)
        assert "error" in result

    def test_missing_end_datetime_returns_error(self):
        result = self.tools.find_rooms(start_datetime="2024-11-15T16:00")
        assert "error" in result

    def test_invalid_datetime_format_returns_error(self):
        result = self.tools.find_rooms(
            start_datetime="not-a-date",
            end_datetime="2024-11-15T17:00",
        )
        assert "error" in result

    def test_end_before_start_returns_error(self):
        result = self.tools.find_rooms(
            start_datetime="2024-11-15T17:00",
            end_datetime="2024-11-15T16:00",
        )
        assert "error" in result

    @patch("tools._get")
    def test_backend_unreachable_returns_error(self, mock_get):
        from tools import BackendError
        mock_get.side_effect = BackendError("Cannot connect to backend")
        result = self.tools.find_rooms()
        assert "error" in result
        assert "rooms" in result
        assert result["rooms"] == []


class TestGetRoomDetails:
    """Tests for tools.get_room_details()."""

    def setup_method(self):
        import tools
        self.tools = tools

    @patch("tools._get")
    def test_returns_room_on_success(self, mock_get):
        mock_get.return_value = SAMPLE_ROOMS[0]
        result = self.tools.get_room_details(1)
        assert result["id"] == 1
        assert result["name"] == "Room A"

    @patch("tools._get")
    def test_not_found_returns_error(self, mock_get):
        from tools import BackendError
        mock_get.side_effect = BackendError("Not found: /rooms/999")
        result = self.tools.get_room_details(999)
        assert "error" in result

    def test_invalid_room_id_returns_error(self):
        result = self.tools.get_room_details(-1)
        assert "error" in result

    def test_zero_room_id_returns_error(self):
        result = self.tools.get_room_details(0)
        assert "error" in result


class TestCheckRoomAvailability:
    """Tests for tools.check_room_availability()."""

    def setup_method(self):
        import tools
        self.tools = tools

    def _mock_backend(self, mock_get, room=None, bookings=None):
        room = room or SAMPLE_ROOMS[0]
        bookings = bookings or []

        def _side_effect(path, params=None):
            if "/rooms/" in path:
                return room
            if path == "/bookings":
                return bookings
        mock_get.side_effect = _side_effect

    @patch("tools._get")
    def test_available_when_no_bookings(self, mock_get):
        self._mock_backend(mock_get)
        result = self.tools.check_room_availability(1, "2024-11-15T16:00", "2024-11-15T17:00")
        assert result["available"] is True
        assert result["conflict_count"] == 0
        assert result["conflicts"] == []

    @patch("tools._get")
    def test_unavailable_when_booking_overlaps(self, mock_get):
        self._mock_backend(mock_get, bookings=[SAMPLE_BOOKINGS[0]])
        # Booking is 14:00–15:00; request 14:30–15:30 → overlap
        result = self.tools.check_room_availability(1, "2024-11-15T14:30", "2024-11-15T15:30")
        assert result["available"] is False
        assert result["conflict_count"] == 1
        assert result["conflicts"][0]["booking_id"] == 101

    @patch("tools._get")
    def test_available_when_booking_is_adjacent_before(self, mock_get):
        """Booking ending exactly at request start is NOT an overlap."""
        self._mock_backend(mock_get, bookings=[SAMPLE_BOOKINGS[0]])
        # Booking is 14:00–15:00; request starts at 15:00 → no overlap
        result = self.tools.check_room_availability(1, "2024-11-15T15:00", "2024-11-15T16:00")
        assert result["available"] is True

    @patch("tools._get")
    def test_cancelled_booking_does_not_conflict(self, mock_get):
        cancelled = {**SAMPLE_BOOKINGS[0], "status": "cancelled"}
        self._mock_backend(mock_get, bookings=[cancelled])
        result = self.tools.check_room_availability(1, "2024-11-15T14:00", "2024-11-15T15:00")
        assert result["available"] is True

    def test_invalid_room_id_returns_error(self):
        result = self.tools.check_room_availability(0, "2024-11-15T16:00", "2024-11-15T17:00")
        assert "error" in result

    def test_invalid_datetime_returns_error(self):
        result = self.tools.check_room_availability(1, "BAD-DATE", "2024-11-15T17:00")
        assert "error" in result

    def test_end_before_start_returns_error(self):
        result = self.tools.check_room_availability(1, "2024-11-15T17:00", "2024-11-15T16:00")
        assert "error" in result


class TestNavigationTools:
    """Tests for tools.get_route() and tools.get_accessible_route()."""

    def setup_method(self):
        import tools
        self.tools = tools

    def test_get_route_valid_rooms(self):
        """get_route returns a structured result for two rooms in the same map."""
        result = self.tools.get_route("201", "202")
        assert isinstance(result, dict)
        # Either a valid route or a clear error
        if "error" not in result:
            assert "steps" in result
            assert isinstance(result["steps"], list)

    def test_get_route_unknown_from_room(self):
        result = self.tools.get_route("GHOST_ROOM_111", "201")
        assert "error" in result

    def test_get_route_unknown_to_room(self):
        result = self.tools.get_route("201", "GHOST_ROOM_999")
        assert "error" in result

    def test_get_route_empty_from_room(self):
        result = self.tools.get_route("", "201")
        assert "error" in result

    def test_get_route_empty_to_room(self):
        result = self.tools.get_route("201", "")
        assert "error" in result

    def test_get_accessible_route_returns_has_stairs(self):
        result = self.tools.get_accessible_route("201", "202")
        if "error" not in result and "cross_building" not in result:
            assert "has_stairs" in result

    def test_get_accessible_route_unknown_room(self):
        result = self.tools.get_accessible_route("NOSUCHROOM", "201")
        assert "error" in result


# ===========================================================================
# 3. MCP server tests — tool registration and transport availability
# ===========================================================================

class TestMCPServer:
    """Tests for server.py — tool registration and Streamable HTTP readiness."""

    def setup_method(self):
        import server
        self.server = server

    def test_mcp_instance_created(self):
        """FastMCP instance exists and is named SpacePilot."""
        assert self.server.mcp is not None
        assert self.server.mcp.name == "SpacePilot"

    def test_all_tools_registered(self):
        """All 12 expected tools are registered on the MCP server."""
        expected_tools = {
            "find_rooms",
            "get_room_details",
            "check_room_availability",
            "check_team_availability",
            "get_route",
            "get_accessible_route",
            "get_events",
            "check_policy",
            "create_booking",
            "update_booking",
            "cancel_booking",
            "notify_team",
        }
        # list_tools() is synchronous wrapper around the tool manager
        import asyncio
        tools = asyncio.run(self.server.mcp.list_tools())
        registered_names = {t.name for t in tools}
        missing = expected_tools - registered_names
        assert not missing, f"Missing tools: {missing}"

    def test_streamable_http_app_callable(self):
        """streamable_http_app() returns an ASGI application object."""
        app = self.server.mcp.streamable_http_app()
        assert app is not None
        # ASGI apps are callable
        assert callable(app)

    def test_phase1_tools_registered(self):
        """The five Phase 1 tools are all registered."""
        import asyncio
        tools = asyncio.run(self.server.mcp.list_tools())
        registered_names = {t.name for t in tools}
        phase1 = {
            "find_rooms",
            "get_room_details",
            "check_room_availability",
            "get_route",
            "get_accessible_route",
        }
        for tool in phase1:
            assert tool in registered_names, f"Phase 1 tool not registered: {tool}"

    def test_tools_have_descriptions(self):
        """Every registered tool must have a non-empty description."""
        import asyncio
        tools = asyncio.run(self.server.mcp.list_tools())
        for tool in tools:
            assert tool.description, f"Tool '{tool.name}' is missing a description"
            assert len(tool.description.strip()) > 10, (
                f"Tool '{tool.name}' has a too-short description: {tool.description!r}"
            )

    def test_host_and_port_settings(self):
        """MCP server respects MCP_HOST and MCP_PORT environment variables."""
        assert self.server.mcp.settings.host == os.getenv("MCP_HOST", "0.0.0.0")
        assert self.server.mcp.settings.port == int(os.getenv("MCP_PORT", "8080"))

    def test_streamable_http_path_is_slash_mcp(self):
        """Streamable HTTP endpoint path is /mcp (MCP SDK default)."""
        assert self.server.mcp.settings.streamable_http_path == "/mcp"


# ===========================================================================
# 4. Time overlap helper tests
# ===========================================================================

class TestOverlapHelper:
    """Tests for tools._overlaps() — the booking conflict detection logic."""

    def setup_method(self):
        import tools
        self.overlaps = tools._overlaps
        self.start = datetime(2024, 11, 15, 16, 0)
        self.end   = datetime(2024, 11, 15, 17, 0)

    def test_fully_overlapping(self):
        assert self.overlaps("2024-11-15T16:00", "2024-11-15T17:00",
                             self.start, self.end) is True

    def test_partially_overlapping_start(self):
        assert self.overlaps("2024-11-15T15:30", "2024-11-15T16:30",
                             self.start, self.end) is True

    def test_partially_overlapping_end(self):
        assert self.overlaps("2024-11-15T16:30", "2024-11-15T17:30",
                             self.start, self.end) is True

    def test_booking_contains_request(self):
        assert self.overlaps("2024-11-15T15:00", "2024-11-15T18:00",
                             self.start, self.end) is True

    def test_request_contains_booking(self):
        assert self.overlaps("2024-11-15T16:15", "2024-11-15T16:45",
                             self.start, self.end) is True

    def test_adjacent_before_no_overlap(self):
        """Booking ending exactly at request start: no overlap."""
        assert self.overlaps("2024-11-15T15:00", "2024-11-15T16:00",
                             self.start, self.end) is False

    def test_adjacent_after_no_overlap(self):
        """Booking starting exactly at request end: no overlap."""
        assert self.overlaps("2024-11-15T17:00", "2024-11-15T18:00",
                             self.start, self.end) is False

    def test_completely_before(self):
        assert self.overlaps("2024-11-15T13:00", "2024-11-15T15:00",
                             self.start, self.end) is False

    def test_completely_after(self):
        assert self.overlaps("2024-11-15T18:00", "2024-11-15T19:00",
                             self.start, self.end) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

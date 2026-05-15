"""
test_server.py — Tests for server-level startup assertions and routing.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestRouteToolConsistency:
    """_assert_routes_match_tools must catch mismatches in both directions."""

    def test_passes_with_matching_routes_and_tools(self, isolated_state):
        from task_anchor.server import _assert_routes_match_tools
        # If this raises, the route table and tool definitions are already out of sync.
        _assert_routes_match_tools()

    def test_raises_when_tool_has_no_route(self, isolated_state):
        from task_anchor.server import _assert_routes_match_tools
        from task_anchor.tools import get_tool_definitions
        from mcp.types import Tool

        extra_tool = Tool(
            name="orphaned_tool",
            description="A tool with no handler.",
            inputSchema={"type": "object", "properties": {}},
        )
        original = get_tool_definitions()

        with patch(
            "task_anchor.server.get_tool_definitions",
            return_value=original + [extra_tool],
        ):
            with pytest.raises(AssertionError, match="Route/tool mismatch"):
                _assert_routes_match_tools()

    def test_raises_when_route_has_no_tool(self, isolated_state):
        from task_anchor.server import _assert_routes_match_tools, _ROUTES

        _ROUTES["ghost_route"] = lambda _: None
        try:
            with pytest.raises(AssertionError, match="Route/tool mismatch"):
                _assert_routes_match_tools()
        finally:
            del _ROUTES["ghost_route"]

"""
server.py — MCP server wiring and entry point.
Single responsibility: register tools, route calls, start stdio loop.
No business logic lives here.
"""

from __future__ import annotations

import argparse
import asyncio
import traceback
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .handlers import (
    handle_drift_detect,
    handle_drift_history_log,
    handle_flow_mode_activate,
    handle_flow_mode_deactivate,
    handle_get_tone,
    handle_parked_add,
    handle_parked_list,
    handle_scope_validate_edit,
    handle_set_tone,
    handle_task_complete,
    handle_task_lock_create,
    handle_task_lock_status,
)
from .handlers_session import handle_session_checkpoint, handle_session_resume
from .config import DRIFT_HISTORY, PARKED_FILE, SESSION_LOG_FILE, SKILL_DIR, STREAK_FILE
from .storage import initialise_state_files
from .tools import get_tool_definitions

# ---------------------------------------------------------------------------
# Route table — maps tool name → handler coroutine.
# Adding a new tool means: add schema to tools.py, handler to handlers.py,
# and one entry here. Nothing else changes.
# ---------------------------------------------------------------------------

_ROUTES: Dict[str, Any] = {
    "task_lock_create":   lambda args: handle_task_lock_create(args),
    "task_lock_status":   lambda _:    handle_task_lock_status(),
    "drift_detect":       lambda args: handle_drift_detect(args),
    "parked_add":         lambda args: handle_parked_add(args),
    "parked_list":        lambda args: handle_parked_list(args),
    "task_complete":      lambda args: handle_task_complete(args),
    "session_checkpoint": lambda args: handle_session_checkpoint(args),
    "session_resume":     lambda _:    handle_session_resume(),
    "scope_validate_edit": lambda args: handle_scope_validate_edit(args),
    "drift_history_log":  lambda args: handle_drift_history_log(args),
    "set_tone":           lambda args: handle_set_tone(args),
    "get_tone":           lambda _:    handle_get_tone(),
    "flow_mode_activate": lambda args: handle_flow_mode_activate(args),
    "flow_mode_deactivate": lambda _:  handle_flow_mode_deactivate(),
}


def _error(msg: str) -> List[TextContent]:
    return [TextContent(type="text", text=msg)]


def _assert_routes_match_tools() -> None:
    tool_names = {t.name for t in get_tool_definitions()}
    route_names = set(_ROUTES)
    if tool_names != route_names:
        raise AssertionError(
            f"Route/tool mismatch — "
            f"tools without routes: {tool_names - route_names!r}, "
            f"routes without tools: {route_names - tool_names!r}"
        )


# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------

class TaskAnchorServer:
    def __init__(self) -> None:
        self._server = Server("task-anchor")
        initialise_state_files(SKILL_DIR, PARKED_FILE, SESSION_LOG_FILE, DRIFT_HISTORY, STREAK_FILE)
        _assert_routes_match_tools()
        self._register_handlers()

    def _register_handlers(self) -> None:

        @self._server.list_tools()
        async def list_tools():
            return get_tool_definitions()

        @self._server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            route = _ROUTES.get(name)
            if route is None:
                return _error(f"⚓ UNKNOWN TOOL: {name}")
            try:
                return await route(arguments or {})
            except Exception as exc:
                tb = traceback.format_exc()
                return _error(f"⚓ SYSTEM ERROR in {name}: {exc}\n\n{tb}")

    async def run(self) -> None:
        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                self._server.create_initialization_options(),
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Synchronous entry point — called by the `task-anchor` console script."""
    parser = argparse.ArgumentParser(
        prog="task-anchor",
        description=(
            "Task Anchor MCP server — ADHD executive function enforcement for Claude Desktop.\n"
            "\n"
            "This is a stdio MCP server, not a CLI tool.\n"
            "It speaks JSON-RPC over stdin/stdout and is launched by Claude Desktop.\n"
            "\n"
            "Configure in claude_desktop_config.json:\n"
            '  { "task-anchor": { "command": "task-anchor" } }'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.parse_args()  # exits cleanly on --help; errors on unknown flags
    asyncio.run(TaskAnchorServer().run())


if __name__ == "__main__":
    main()

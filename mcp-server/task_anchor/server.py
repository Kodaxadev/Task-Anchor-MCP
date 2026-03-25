"""
server.py — MCP server wiring and entry point.
Single responsibility: register tools, route calls, start stdio loop.
No business logic lives here.
"""

from __future__ import annotations

import asyncio
import traceback
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .handlers import (
    handle_drift_detect,
    handle_drift_history_log,
<<<<<<< HEAD
    handle_flow_mode_activate,
    handle_flow_mode_deactivate,
    handle_get_tone,
=======
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
    handle_parked_add,
    handle_parked_list,
    handle_scope_validate_edit,
    handle_session_checkpoint,
    handle_session_resume,
<<<<<<< HEAD
    handle_set_tone,
=======
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
    handle_task_complete,
    handle_task_lock_create,
    handle_task_lock_status,
)
from .models import DRIFT_HISTORY, PARKED_FILE, SESSION_LOG_FILE, SKILL_DIR, STREAK_FILE
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
<<<<<<< HEAD
    "set_tone":           lambda args: handle_set_tone(args),
    "get_tone":           lambda _:    handle_get_tone(),
    "flow_mode_activate": lambda args: handle_flow_mode_activate(args),
    "flow_mode_deactivate": lambda _:  handle_flow_mode_deactivate(),
=======
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
}


def _error(msg: str) -> List[TextContent]:
    return [TextContent(type="text", text=msg)]


# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------

class TaskAnchorServer:
    def __init__(self) -> None:
        self._server = Server("task-anchor")
        initialise_state_files(SKILL_DIR, PARKED_FILE, SESSION_LOG_FILE, DRIFT_HISTORY, STREAK_FILE)
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
    server = TaskAnchorServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

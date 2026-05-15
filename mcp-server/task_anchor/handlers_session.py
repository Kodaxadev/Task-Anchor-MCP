"""
handlers_session.py — Session lifecycle handler coroutines.
Single responsibility: session_checkpoint and session_resume tool behaviour.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Any, Dict, List

from mcp.types import TextContent

from .helpers import get_git_branch, update_session_log
from .models import SESSION_FILE, SKILL_DIR, TASK_LOCK_FILE
from .storage import read_json, write_json
from .tone import msg


def _text(body: str) -> List[TextContent]:
    return [TextContent(type="text", text=body.strip())]


# ---------------------------------------------------------------------------
# Git helper — isolated so it's easy to test and reason about independently.
# ---------------------------------------------------------------------------

def _run_git_checkpoint(commit_msg: str) -> str:
    """Stage state files and commit. Returns a human-readable status string."""
    try:
        subprocess.run(
            ["git", "add", str(SKILL_DIR)],
            check=False, timeout=10,
        )
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg, "--no-verify"],
            check=False, timeout=10,
            capture_output=True,
        )
        if result.returncode == 0:
            return f"committed — {commit_msg[:50]}"
        if result.returncode == 1:
            return "skipped — nothing to commit"
        return f"skipped — commit failed (exit {result.returncode})"
    except FileNotFoundError:
        return "skipped — git not found"
    except subprocess.TimeoutExpired:
        return "skipped — timeout"


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

async def handle_session_checkpoint(args: Dict[str, Any]) -> List[TextContent]:
    if not TASK_LOCK_FILE.exists() and not args.get("force"):
        return _text(msg("checkpoint_no_lock"))

    task_data = read_json(TASK_LOCK_FILE)

    session_data = {
        "timestamp":         datetime.now().isoformat(),
        "emotional_state":   args["emotional_state"],
        "next_micro_action": args["next_micro_action"],
        "blocker_note":      args.get("blocker_note", ""),
        "git_branch":        get_git_branch(),
        "task":              task_data,
    }

    write_json(SESSION_FILE, session_data)
    update_session_log(session_data)

    task_title = (task_data or {}).get("building", "unknown")[:40]
    commit_msg = (
        f"session-anchor: {task_title} | "
        f"Next: {args['next_micro_action'][:30]} | "
        f"State: {args['emotional_state']}"
    )
    git_status = _run_git_checkpoint(commit_msg)

    warning = ""
    if args["emotional_state"] in ("stuck", "frustrated"):
        warning = msg("checkpoint_stuck_warn")

    return _text(msg("checkpoint_saved",
        emotional_state=args["emotional_state"],
        next_action=args["next_micro_action"],
        git_status=git_status,
        warning=warning,
    ))


async def handle_session_resume() -> List[TextContent]:
    session = read_json(SESSION_FILE)
    if session is None:
        return _text(msg("resume_no_session"))

    task = session.get("task") or {}
    emotional = session["emotional_state"]

    kwargs = dict(
        timestamp=session["timestamp"][:16],
        building=task.get("building", "Unknown"),
        emotional=emotional.upper(),
        next_action=session["next_micro_action"],
    )

    if emotional in ("stuck", "frustrated"):
        kwargs["blocker"] = session.get("blocker_note") or "Not recorded"
        return _text(msg("resume_stuck", **kwargs))

    return _text(msg("resume_normal", **kwargs))

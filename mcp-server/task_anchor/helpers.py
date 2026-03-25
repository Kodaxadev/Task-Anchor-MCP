"""
helpers.py — Internal utility functions shared by handler coroutines.
Single responsibility: extract common logic from handlers to keep that
module under 400 lines and maintain one-concern-per-function structure.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict, Optional

from .models import (
    PARKED_FILE,
    SESSION_FILE,
    SESSION_LOG_FILE,
    TASK_LOCK_FILE,
    TaskLock,
)
from .storage import read_json


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def get_git_branch() -> str | None:
    """Return the current git branch name, or None if unavailable."""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).decode().strip()
        return branch or None
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def count_parked() -> int:
    """Count parked idea entries (lines starting with '- [') in PARKED.md."""
    if not PARKED_FILE.exists():
        return 0
    with open(PARKED_FILE, encoding="utf-8") as f:
        return sum(1 for line in f if line.startswith("- ["))


def load_lock() -> TaskLock | None:
    """Load and deserialise the current task lock, or None if absent."""
    data = read_json(TASK_LOCK_FILE)
    return TaskLock.from_dict(data) if data else None


def extract_parked_timestamp(line: str) -> str:
    """Pull the ISO timestamp from a parked entry line.

    Expected format: '- [URGENCY] 2026-03-25T14:30:00 | category: idea'
    Returns empty string if parsing fails (sorts before any real timestamp).
    """
    try:
        after_bracket = line.split("] ", 1)[1]
        timestamp = after_bracket.split(" | ", 1)[0].strip()
        return timestamp
    except (IndexError, ValueError):
        return ""


# ---------------------------------------------------------------------------
# Session log writer
# ---------------------------------------------------------------------------

def update_session_log(data: Dict[str, Any]) -> None:
    """Write the human-readable SESSION_LOG.md, preserving history section."""
    header = (
        "# 📋 SESSION LOG\n"
        "*The breadcrumb trail between fragmented time*\n\n"
        f"## Current Session\n"
        f"**Timestamp:** {data['timestamp'][:16]}\n"
        f"**Task:** {(data.get('task') or {}).get('building', 'No active task')}\n"
        f"**Branch:** {data.get('git_branch', 'none')}\n"
        f"**Emotional State:** {data['emotional_state'].upper()}\n"
        f"**Next Action:** {data['next_micro_action']}\n"
        f"**Blocker:** {data.get('blocker_note') or 'None'}\n\n"
        "---\n"
    )

    history = ""
    if SESSION_LOG_FILE.exists():
        try:
            content = SESSION_LOG_FILE.read_text(encoding="utf-8")
            if "## Previous Sessions" in content:
                history = content.split("## Previous Sessions", 1)[1]
        except OSError:
            pass

    SESSION_LOG_FILE.write_text(
        header + "\n## Previous Sessions" + history,
        encoding="utf-8",
    )

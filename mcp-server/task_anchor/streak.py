"""
streak.py — Daily streak tracking and completion celebration ritual.
Single responsibility: dopamine layer. No task logic, no file routing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .storage import read_json, write_json
from .tone import msg


# ---------------------------------------------------------------------------
# Streak tracking
# ---------------------------------------------------------------------------

def increment_streak(streak_file: Path) -> str:
    """
    Increments streak counter if today hasn't been counted yet.
    Resets the streak if the last completion was not yesterday.
    Returns a formatted status string for display in the completion response.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    data = read_json(
        streak_file,
        default={"current": 0, "last_date": None, "longest": 0, "history": []},
    )

    if data["last_date"] == today:
        return msg("streak_today", current=data["current"])

    # Reset streak if the user missed a day (not consecutive)
    if data["last_date"] is not None:
        try:
            last = datetime.strptime(data["last_date"], "%Y-%m-%d")
            today_dt = datetime.strptime(today, "%Y-%m-%d")
            if (today_dt - last).days != 1:
                data["current"] = 0  # will become 1 after increment below
        except ValueError:
            data["current"] = 0

    data["current"] += 1
    data["last_date"] = today
    data["history"].append(today)

    if data["current"] > data["longest"]:
        data["longest"] = data["current"]

    write_json(streak_file, data)

    fire = "🔥" * min(data["current"], 5)
    return msg("streak_new",
        fire=fire, current=data["current"], longest=data["longest"],
    )



# ---------------------------------------------------------------------------
# Completion celebration — minimalist industrial aesthetic.
# Skipped entirely if TASK_ANCHOR_SILENT=1 is set.
# The celebration runs BEFORE the lock file is deleted, so rewards config
# can still be read from it. Call this before task_lock_file.unlink().
# ---------------------------------------------------------------------------

_ASCII_ANCHORED = r"""
   _   _   _   _   _   _   _   _
  / \ / \ / \ / \ / \ / \ / \ / \
 ( A ( N ( C ( H ( O ( R ( E ( D )
  \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
"""


def completion_celebration(task_name: str, rewards_config: dict | None = None) -> None:
    """
    Writes a celebration to stderr when a task is validated complete.
    stderr is used intentionally — stdout is the MCP JSON-RPC channel and
    must never receive non-JSON output.

    Args:
        task_name:      The `building` field from the completed TaskLock.
        rewards_config: The rewards dict from the lock (read BEFORE unlink).
    """
    if os.environ.get("TASK_ANCHOR_SILENT") == "1":
        return

    config = rewards_config or {}
    if config.get("visual") == "none":
        return

    _err = sys.stderr

    print("\033[32m", end="", file=_err)  # Green

    # Try figlet — no shell=True needed; pass args as list.
    try:
        result = subprocess.run(
            ["figlet", "-f", "small", "ANCHORED"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout, file=_err)
        else:
            print(_ASCII_ANCHORED, file=_err)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        print(_ASCII_ANCHORED, file=_err)

    print(f"\033[90m{task_name}\033[0m", file=_err)
    print("\033[0m", end="", file=_err)  # Reset colour

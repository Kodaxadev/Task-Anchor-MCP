"""
flow.py — Flow mode logic: activate, check, and auto-expire.
Single responsibility: manage the temporary drift-suspension state.

Flow mode suspends drift detection for a user-specified duration,
letting hyperfocused users work without interruption. Scope enforcement
remains active (safety net, not a cage).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .models import FLOW_MODE_FILE
from .storage import read_json, write_json


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FLOW_MINUTES = 120   # hard cap — even hyperfocus needs a check-in
DEFAULT_FLOW_MINUTES = 30


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def activate(duration_minutes: int | None = None) -> tuple[int, str]:
    """Enable flow mode. Returns (duration, expiry_iso)."""
    minutes = min(duration_minutes or DEFAULT_FLOW_MINUTES, MAX_FLOW_MINUTES)
    expires = datetime.now() + timedelta(minutes=minutes)
    write_json(FLOW_MODE_FILE, {
        "active": True,
        "activated_at": datetime.now().isoformat(),
        "expires_at": expires.isoformat(),
        "duration_minutes": minutes,
    })
    return minutes, expires.strftime("%H:%M")


def deactivate() -> None:
    """Explicitly end flow mode."""
    if FLOW_MODE_FILE.exists():
        FLOW_MODE_FILE.unlink(missing_ok=True)


def is_active() -> tuple[bool, str]:
    """Check if flow mode is currently active.

    Returns (is_active, expiry_display).
    Auto-expires if past the deadline.
    """
    data = read_json(FLOW_MODE_FILE)
    if not data or not data.get("active"):
        return False, ""

    try:
        expires = datetime.fromisoformat(data["expires_at"])
    except (KeyError, ValueError):
        deactivate()
        return False, ""

    if datetime.now() >= expires:
        deactivate()
        return False, "expired"

    return True, expires.strftime("%H:%M")

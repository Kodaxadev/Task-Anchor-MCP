"""
tone.py — Configurable tone system for all user-facing messages.
Single responsibility: load/save tone preference, resolve message keys
to the active tone variant.

Tones:
  strict      — Original enforcement language (VIOLATION, REJECTED, etc.)
  supportive  — Warm coaching voice, acknowledges effort, preserves agency
  minimal     — Facts only, no emotional language, shortest possible output
"""

from __future__ import annotations

from typing import Any

from .models import TONE_FILE
from .storage import read_json, write_json
from .messages import MESSAGES


# ---------------------------------------------------------------------------
# Valid tones — order matters for display
# ---------------------------------------------------------------------------

VALID_TONES = ("strict", "supportive", "minimal")
DEFAULT_TONE = "supportive"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def get_tone() -> str:
    """Return the user's current tone preference."""
    data = read_json(TONE_FILE, default={})
    tone = data.get("tone", DEFAULT_TONE)
    return tone if tone in VALID_TONES else DEFAULT_TONE


def set_tone(tone: str) -> str:
    """Persist a tone preference. Returns the normalised tone name."""
    tone = tone.strip().lower()
    if tone not in VALID_TONES:
        raise ValueError(
            f"Unknown tone {tone!r}. Choose from: {', '.join(VALID_TONES)}"
        )
    write_json(TONE_FILE, {"tone": tone})
    return tone


# ---------------------------------------------------------------------------
# Message resolution
# ---------------------------------------------------------------------------

def msg(key: str, **kwargs: Any) -> str:
    """Look up a message template by key and format it with kwargs.

    Falls back to 'strict' if the key is missing from the active tone,
    then falls back to a raw f"[{key}]" if the key is completely unknown.
    """
    tone = get_tone()
    templates = MESSAGES.get(key, {})

    template = templates.get(tone) or templates.get("strict") or f"[{key}]"
    try:
        return template.format(**kwargs)
    except KeyError:
        return template

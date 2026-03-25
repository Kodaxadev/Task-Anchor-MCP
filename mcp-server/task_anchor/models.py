"""
models.py — TaskLock dataclass and drift scoring constants.
Single responsibility: data shapes only. Path resolution lives in config.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

# Re-export path constants so existing imports of the form
#   from .models import TASK_LOCK_FILE
# continue to work without changes to other modules.
from .config import (  # noqa: F401
    SKILL_DIR,
    TASK_LOCK_FILE,
    PARKED_FILE,
    SESSION_FILE,
    SESSION_LOG_FILE,
    DRIFT_HISTORY,
    STREAK_FILE,
    EXIT_VALIDATED,
<<<<<<< HEAD
    TONE_FILE,
    FLOW_MODE_FILE,
=======
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
)

# ---------------------------------------------------------------------------
# Drift scoring — weights live here so they're easy to tune without touching
# detection logic.
# ---------------------------------------------------------------------------


# Signals are matched as WHOLE PHRASES (not substrings) in drift.py.
# "rewrite" won't fire inside "overwrite"; "instead" won't fire inside "instantiate".
# Weights reflect how strongly each phrase predicts a context switch vs. being
# normal in-task language. Tune here without touching detection logic.
DRIFT_SIGNALS: dict[str, int] = {
    # Strong scope-switch indicators
    "while we're at it":  5,
    "might as well":      5,
    "new library":        5,
    "different approach": 5,
    # Moderate — directional pivots
    "instead of":         4,
    "what if we":         4,
    "can you also":       4,
    "let's switch":       4,
    "scrap that":         4,
    # Softer signals — need other signals to compound
    "actually":           2,
    "quick question":     2,
    "simpler approach":   3,
    "easier if we":       3,
    "rewrite the":        3,   # "rewrite the X" — directional, not substring noise
}

# Gap penalty is only added when input is clearly off-topic AND substantive.
# Raised from 20 → 40 chars to avoid penalising short focused questions.
DRIFT_GAP_MIN_LENGTH = 40   # chars — below this, gap penalty is skipped entirely
DRIFT_GAP_PENALTY    = 3    # score added when context overlap is low
DRIFT_GAP_MAX_OVERLAP = 2   # overlap below this triggers the penalty

DRIFT_THRESHOLD = 4   # score >= this triggers park+redirect
DRIFT_SCORE_CAP = 10  # display cap so UI label isn't misleading


# ---------------------------------------------------------------------------
# TaskLock — the core domain object. Kept as a plain dataclass so it's
# trivially serialisable with asdict() and reconstructable with **dict.
# The `rewards` field is declared here to prevent the **lock_data TypeError
# that occurred in the original monolith.
# ---------------------------------------------------------------------------

@dataclass
class TaskLock:
    building:        str
    done_criteria:   str
    scope_files:     List[str]
    exit_condition:  str
    locked_at:       str
    status:          str = "active"          # active | suspended | completed
    git_branch:      Optional[str] = None
    emotional_state: Optional[str] = None
    rewards:         dict = field(default_factory=lambda: {
        "visual":     "minimal",
        "sound":      False,
        "git_emoji":  "⚓",
    })

    # ------------------------------------------------------------------
    # Scope validation — checks whether a given path is within any of
    # the declared scope_files entries (prefix match, case-insensitive).
    # ------------------------------------------------------------------

    def validate_scope(self, file_path: str) -> bool:
        abs_file = os.path.abspath(file_path).lower()
        for scope in self.scope_files:
            abs_scope = os.path.abspath(scope).lower()
            if abs_file.startswith(abs_scope):
                return True
        return False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TaskLock":
        # Strip unknown keys so future schema additions don't break old locks.
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

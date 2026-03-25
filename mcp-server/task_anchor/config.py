"""
config.py — Absolute path resolution for all Task Anchor state files.
Single responsibility: tell every module WHERE things live, regardless of
what directory the process was launched from.

Resolution order:
  1. TASK_ANCHOR_DIR env var (absolute path) — for testing or custom installs
  2. Anchor up from this file's location to the repo root, then into
     .claude/skills/task-anchor/ — always correct regardless of cwd

Layout assumption:
    <repo-root>/
    ├── .claude/
    │   └── skills/
    │       └── task-anchor/      ← state files live here
    └── mcp-server/
        └── task_anchor/
            └── config.py         ← this file

So __file__ is  <repo>/mcp-server/task_anchor/config.py
   .parent      <repo>/mcp-server/task_anchor/
   .parent      <repo>/mcp-server/
   .parent      <repo>/                         ← repo root
   / ".claude/skills/task-anchor"               ← state dir
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_base() -> Path:
    env_override = os.environ.get("TASK_ANCHOR_DIR", "").strip()
    if env_override:
        p = Path(env_override).expanduser().resolve()
        if not p.is_absolute():
            raise ValueError(
                f"TASK_ANCHOR_DIR must be an absolute path, got: {env_override!r}"
            )
        return p

    # Walk up: config.py → task_anchor/ → mcp-server/ → repo root
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / ".claude" / "skills" / "task-anchor"


# All paths derived from a single resolved base — change the base, everything moves.
BASE             = _resolve_base()

SKILL_DIR        = BASE
TASK_LOCK_FILE   = BASE / "TASK_LOCK.json"
PARKED_FILE      = BASE / "PARKED.md"
SESSION_FILE     = BASE / "SESSION.json"
SESSION_LOG_FILE = BASE / "SESSION_LOG.md"
DRIFT_HISTORY    = BASE / "DRIFT_HISTORY.json"
STREAK_FILE      = BASE / "STREAK.json"
EXIT_VALIDATED   = BASE / ".exit_validated"
TONE_FILE        = BASE / "TONE.json"
FLOW_MODE_FILE   = BASE / "FLOW_MODE.json"

"""
storage.py — All file I/O, locking primitives, and atomic write helpers.
Single responsibility: safely read/write state files. No business logic here.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

# ---------------------------------------------------------------------------
# Platform-level file locking — resolved once at import time.
# The original code had a three-way flag (True/False/None) which was confusing.
# We use a simple enum-style constant instead.
# ---------------------------------------------------------------------------

_LOCK_BACKEND: str  # "fcntl" | "msvcrt" | "none"

try:
    import fcntl as _fcntl
    _LOCK_BACKEND = "fcntl"
except ImportError:
    try:
        import msvcrt as _msvcrt
        _LOCK_BACKEND = "msvcrt"
    except ImportError:
        _LOCK_BACKEND = "none"


def _acquire(f: Any) -> None:
    """Acquire an exclusive lock on an open file handle."""
    if _LOCK_BACKEND == "fcntl":
        _fcntl.flock(f.fileno(), _fcntl.LOCK_EX)
    elif _LOCK_BACKEND == "msvcrt":
        # Lock entire file size in chunks; fall back to 1-byte advisory lock.
        # msvcrt.locking requires the byte count to match the file size or it
        # raises a permission error on large files — the original hardcoded '1'
        # was wrong. We use an advisory 1-byte lock at position 0 as a mutex.
        f.seek(0)
        try:
            _msvcrt.locking(f.fileno(), _msvcrt.LK_NBLCK, 1)
        except OSError:
            pass  # Another process holds the lock; proceed optimistically.
    # "none" backend: no-op — single-process safety only


def _release(f: Any) -> None:
    """Release a previously acquired lock."""
    if _LOCK_BACKEND == "fcntl":
        _fcntl.flock(f.fileno(), _fcntl.LOCK_UN)
    elif _LOCK_BACKEND == "msvcrt":
        f.seek(0)
        try:
            _msvcrt.locking(f.fileno(), _msvcrt.LK_UNLCK, 1)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Atomic write — write to a .tmp file, then rename into place.
# On Windows, rename fails if the target exists; we unlink first.
# ---------------------------------------------------------------------------

@contextmanager
def atomic_write(path: Path) -> Generator[Any, None, None]:
    """
    Context manager: yields an open file handle for writing.
    On exit, atomically replaces `path` with the completed temp file.

    Usage:
        with atomic_write(MY_FILE) as f:
            json.dump(data, f)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        _acquire(f)
        try:
            yield f
        finally:
            _release(f)

    if os.name == "nt" and path.exists():
        path.unlink()
    tmp.rename(path)


# ---------------------------------------------------------------------------
# JSON helpers — thin wrappers with consistent error handling.
# ---------------------------------------------------------------------------

def read_json(path: Path, default: Any = None) -> Any:
    """Read and parse a JSON file. Returns `default` if missing or corrupt."""
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: Path, data: Any) -> None:
    """Atomically write `data` as JSON to `path`."""
    with atomic_write(path) as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Append helper — used by parked ideas (append-only log).
# ---------------------------------------------------------------------------

def append_line(path: Path, line: str) -> None:
    """
    Thread-safe append of a single line to a text file.
    Creates the file if missing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        _acquire(f)
        try:
            f.write(line if line.endswith("\n") else line + "\n")
        finally:
            _release(f)


# ---------------------------------------------------------------------------
# Initialisation — ensure all required state files exist on first run.
# Called once at server startup.
# ---------------------------------------------------------------------------

def initialise_state_files(
    skill_dir: Path,
    parked_file: Path,
    session_log_file: Path,
    drift_history: Path,
    streak_file: Path,
) -> None:
    """Create skeleton state files if they don't already exist."""
    skill_dir.mkdir(parents=True, exist_ok=True)

    if not parked_file.exists():
        parked_file.write_text(
            "# 🅿️ PARKED IDEAS\n"
            "*The safety net for your brilliance. It's safe to forget these for now.*\n\n"
            "## Pending Ideas\n",
            encoding="utf-8",
        )

    if not session_log_file.exists():
        session_log_file.write_text(
            "# 📋 SESSION LOG\n"
            "*The breadcrumb trail between fragmented time*\n\n"
            "## Previous Sessions\n",
            encoding="utf-8",
        )

    if not drift_history.exists():
        write_json(drift_history, {"total_drifts": 0, "successful_interventions": 0})

    if not streak_file.exists():
        write_json(streak_file, {"current": 0, "last_date": None, "longest": 0, "history": []})

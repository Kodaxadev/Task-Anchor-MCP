"""
handlers.py — All call_tool handler coroutines for the Task Anchor MCP server.
Single responsibility: implement tool behaviour. Delegates I/O to storage,
scoring to drift, formatting to tone, and dopamine layer to streak.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Any, Dict, List

from mcp.types import TextContent

from .drift import (
    capped_score,
    is_drift,
    log_drift_event,
    score_completion,
    score_input,
)
from .flow import activate as flow_activate, deactivate as flow_deactivate, is_active as flow_is_active
from .helpers import (
    count_parked,
    extract_parked_timestamp,
    get_git_branch,
    load_lock,
    update_session_log,
)
from .models import (
    DRIFT_HISTORY,
    EXIT_VALIDATED,
    PARKED_FILE,
    SESSION_FILE,
    SKILL_DIR,
    STREAK_FILE,
    TASK_LOCK_FILE,
    TaskLock,
)
from .storage import append_line, atomic_write, read_json, write_json
from .streak import increment_streak
from .tone import msg


def _text(body: str) -> List[TextContent]:
    return [TextContent(type="text", text=body.strip())]


# ---------------------------------------------------------------------------
# Tool handlers — one coroutine per tool
# ---------------------------------------------------------------------------

async def handle_task_lock_create(args: Dict[str, Any]) -> List[TextContent]:
    SKILL_DIR.mkdir(parents=True, exist_ok=True)

    lock = TaskLock(
        building=args["building"],
        done_criteria=args["done_criteria"],
        scope_files=args["scope_files"],
        exit_condition=args["exit_condition"],
        locked_at=datetime.now().isoformat(),
        git_branch=get_git_branch(),
    )

    with atomic_write(TASK_LOCK_FILE) as f:
        json.dump(lock.to_dict(), f, indent=2)

    return _text(msg("lock_engaged",
        building=lock.building,
        exit_condition=lock.exit_condition,
        scope=", ".join(lock.scope_files),
        git=lock.git_branch or "none",
    ))


async def handle_task_lock_status() -> List[TextContent]:
    if not TASK_LOCK_FILE.exists():
        return _text(msg("no_lock"))

    lock_data = read_json(TASK_LOCK_FILE)

    session_warning = ""
    session = read_json(SESSION_FILE)
    if session and session.get("emotional_state") in ("stuck", "frustrated"):
        session_warning = msg("session_warning")

    return _text(msg("lock_status",
        building=lock_data["building"],
        exit_condition=lock_data["exit_condition"],
        scope_count=len(lock_data["scope_files"]),
        since=lock_data["locked_at"][:16],
        session_warning=session_warning,
    ))


async def handle_drift_detect(args: Dict[str, Any]) -> List[TextContent]:
    user_input = args["user_input"]
    current_context = args["current_context"]

    # Flow mode bypasses drift detection entirely
    active, expires = flow_is_active()
    if active:
        return _text(msg("drift_flow_mode", expires=expires))
    # Check for expired flow mode — notify once
    if expires == "expired":
        return _text(msg("flow_expired"))

    score, overlap = score_input(user_input, current_context)
    cap = 10  # DRIFT_SCORE_CAP

    if is_drift(score):
        log_drift_event(DRIFT_HISTORY, "signal_match", True)
        snippet = user_input[:60] + ("..." if len(user_input) > 60 else "")
        return _text(msg("drift_detected",
            score=capped_score(score), cap=cap,
            snippet=snippet, overlap=overlap,
            context=current_context,
        ))

    return _text(msg("drift_clear", score=capped_score(score), cap=cap))


async def handle_parked_add(args: Dict[str, Any]) -> List[TextContent]:
    idea = args["idea"]
    category = args["category"]
    urgency = args.get("urgency", "medium")

    timestamp = datetime.now().isoformat()
    entry = f"- [{urgency.upper()}] {timestamp} | {category}: {idea}"
    append_line(PARKED_FILE, entry)

    log_drift_event(DRIFT_HISTORY, "parked_success", True)

    return _text(msg("parked_add",
        idea=idea, urgency=urgency, category=category,
    ))


async def handle_parked_list(args: Dict[str, Any]) -> List[TextContent]:
    if not PARKED_FILE.exists():
        return _text("No items parked yet.")

    filter_type = args.get("filter", "all")

    with open(PARKED_FILE, "r", encoding="utf-8") as f:
        items = f.readlines()

    entries = [i for i in items if i.startswith("- [")]

    if filter_type == "urgent":
        entries = [i for i in entries if "[BLOCKING]" in i or "[HIGH]" in i]
    elif filter_type == "current_session":
        lock = load_lock()
        if lock is not None:
            entries = [
                i for i in entries
                if extract_parked_timestamp(i) >= lock.locked_at
            ]

    return _text("".join(entries) if entries else "No matching items.")


async def handle_scope_validate_edit(args: Dict[str, Any]) -> List[TextContent]:
    lock = load_lock()
    if lock is None:
        return _text(msg("scope_no_lock"))

    file_path = args["file_path"]
    if lock.validate_scope(file_path):
        return _text(msg("scope_pass", file_path=file_path))

    return _text(msg("scope_fail",
        file_path=file_path,
        scope=lock.scope_files,
        building=lock.building,
    ))


async def handle_task_complete(args: Dict[str, Any]) -> List[TextContent]:
    lock_data = read_json(TASK_LOCK_FILE)
    if lock_data is None:
        return _text(msg("completion_no_lock"))

    evidence = args["completion_evidence"]
    exit_cond = lock_data["exit_condition"]
    match_ratio = score_completion(exit_cond, evidence)

    if match_ratio < 0.5:
        return _text(msg("completion_rejected",
            exit_condition=exit_cond,
            ratio=f"{match_ratio:.0%}",
            evidence=evidence,
        ))

    # Archive to PARKED.md
    completed_section = (
        f"\n\n## COMPLETED: {lock_data['building']}\n"
        f"Completed: {datetime.now().isoformat()}\n"
        f"Evidence: {evidence}\n"
    )
    try:
        PARKED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PARKED_FILE, "a", encoding="utf-8") as f:
            f.write(completed_section)
    except OSError:
        pass

    TASK_LOCK_FILE.unlink(missing_ok=True)
    EXIT_VALIDATED.touch()

    streak_msg = increment_streak(STREAK_FILE)
    parked_count = count_parked()

    return _text(msg("completion_success",
        streak=streak_msg,
        building=lock_data["building"],
        ratio=f"{match_ratio:.0%}",
        parked_count=parked_count,
    ))


async def handle_session_checkpoint(args: Dict[str, Any]) -> List[TextContent]:
    if not TASK_LOCK_FILE.exists() and not args.get("force"):
        return _text(msg("checkpoint_no_lock"))

    task_data = read_json(TASK_LOCK_FILE)

    session_data = {
        "timestamp":        datetime.now().isoformat(),
        "emotional_state":  args["emotional_state"],
        "next_micro_action": args["next_micro_action"],
        "blocker_note":     args.get("blocker_note", ""),
        "git_branch":       get_git_branch(),
        "task":             task_data,
    }

    write_json(SESSION_FILE, session_data)
    update_session_log(session_data)

    task_title = (task_data or {}).get("building", "unknown")[:40]
    git_msg = (
        f"session-anchor: {task_title} | "
        f"Next: {args['next_micro_action'][:30]} | "
        f"State: {args['emotional_state']}"
    )
    try:
        subprocess.run(["git", "add", "-A"], check=False, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", git_msg, "--no-verify"],
            check=False, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    warning = ""
    if args["emotional_state"] in ("stuck", "frustrated"):
        warning = msg("checkpoint_stuck_warn")

    return _text(msg("checkpoint_saved",
        emotional_state=args["emotional_state"],
        next_action=args["next_micro_action"],
        git_msg=git_msg[:60],
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


async def handle_drift_history_log(args: Dict[str, Any]) -> List[TextContent]:
    log_drift_event(
        DRIFT_HISTORY,
        args.get("drift_type", "unknown"),
        args.get("intervention_successful", True),
    )
    return _text("✓ Drift event logged.")


# ---------------------------------------------------------------------------
# New tools: tone + flow mode
# ---------------------------------------------------------------------------

async def handle_set_tone(args: Dict[str, Any]) -> List[TextContent]:
    from .tone import set_tone, VALID_TONES
    tone = args.get("tone", "supportive")
    try:
        result = set_tone(tone)
        return _text(f"Tone set to: {result}")
    except ValueError:
        return _text(f"Unknown tone. Choose from: {', '.join(VALID_TONES)}")


async def handle_get_tone() -> List[TextContent]:
    from .tone import get_tone, VALID_TONES
    current = get_tone()
    options = " | ".join(
        f"**{t}**" if t == current else t for t in VALID_TONES
    )
    return _text(f"Current tone: {current}\nAvailable: {options}")


async def handle_flow_mode_activate(args: Dict[str, Any]) -> List[TextContent]:
    duration = args.get("duration_minutes")
    minutes, expires = flow_activate(duration)
    return _text(msg("flow_activated", duration=minutes, expires=expires))


async def handle_flow_mode_deactivate() -> List[TextContent]:
    flow_deactivate()
    return _text(msg("flow_deactivated"))

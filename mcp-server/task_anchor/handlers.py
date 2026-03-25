"""
handlers.py — All call_tool handler coroutines for the Task Anchor MCP server.
Single responsibility: implement tool behaviour. Delegates I/O to storage,
<<<<<<< HEAD
scoring to drift, formatting to tone, and dopamine layer to streak.
=======
scoring to drift, and dopamine layer to streak.
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Any, Dict, List

<<<<<<< HEAD
from mcp.types import TextContent

from .drift import (
    capped_score,
=======

from mcp.types import TextContent

from .drift import (
    format_clear_response,
    format_drift_response,
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
    is_drift,
    log_drift_event,
    score_completion,
    score_input,
)
<<<<<<< HEAD
from .flow import activate as flow_activate, deactivate as flow_deactivate, is_active as flow_is_active
=======
from .models import (
    DRIFT_HISTORY,
    EXIT_VALIDATED,
    PARKED_FILE,
    SESSION_FILE,
    SESSION_LOG_FILE,
    SKILL_DIR,
    STREAK_FILE,
    TASK_LOCK_FILE,
    TaskLock,
)
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
from .helpers import (
    count_parked,
    extract_parked_timestamp,
    get_git_branch,
    load_lock,
    update_session_log,
)
<<<<<<< HEAD
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
=======
from .storage import append_line, atomic_write, read_json, write_json
from .streak import completion_celebration, increment_streak


def _text(msg: str) -> List[TextContent]:
    return [TextContent(type="text", text=msg.strip())]
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


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

<<<<<<< HEAD
    return _text(msg("lock_engaged",
        building=lock.building,
        exit_condition=lock.exit_condition,
        scope=", ".join(lock.scope_files),
        git=lock.git_branch or "none",
    ))
=======
    return _text(
        f"⚓ TASK LOCK ENGAGED\n\n"
        f"BUILDING: {lock.building}\n"
        f"EXIT:     {lock.exit_condition}\n"
        f"SCOPE:    {', '.join(lock.scope_files)}\n"
        f"GIT:      {lock.git_branch or 'none'}\n\n"
        f"STATUS: Active enforcement enabled.\n"
        f"DRIFT DETECTION: Armed."
    )
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


async def handle_task_lock_status() -> List[TextContent]:
    if not TASK_LOCK_FILE.exists():
<<<<<<< HEAD
        return _text(msg("no_lock"))
=======
        return _text(
            "⚓ NO TASK LOCK\n"
            "STATUS: Drift imminent. Create lock immediately.\n"
            "VIOLATION: Cannot proceed with coding tasks."
        )
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b

    lock_data = read_json(TASK_LOCK_FILE)

    session_warning = ""
    session = read_json(SESSION_FILE)
    if session and session.get("emotional_state") in ("stuck", "frustrated"):
<<<<<<< HEAD
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
=======
        session_warning = (
            "\n⚠️ WARNING: Last session ended in a stuck state. "
            "Review the blocker note before resuming."
        )

    return _text(
        f"⚓ LOCKED: {lock_data['building']}\n"
        f"🎯 EXIT:  {lock_data['exit_condition']}\n"
        f"📁 SCOPE: {len(lock_data['scope_files'])} file(s)\n"
        f"🕒 Since: {lock_data['locked_at'][:16]}"
        f"{session_warning}\n\n"
        f"Enforcement: ACTIVE"
    )


async def handle_drift_detect(args: Dict[str, Any]) -> List[TextContent]:
    user_input      = args["user_input"]
    current_context = args["current_context"]

    score, overlap = score_input(user_input, current_context)

    if is_drift(score):
        log_drift_event(DRIFT_HISTORY, "signal_match", True)
        return _text(format_drift_response(user_input, current_context, score, overlap))

    return _text(format_clear_response(score))


async def handle_parked_add(args: Dict[str, Any]) -> List[TextContent]:
    idea     = args["idea"]
    category = args["category"]
    urgency  = args.get("urgency", "medium")
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b

    timestamp = datetime.now().isoformat()
    entry = f"- [{urgency.upper()}] {timestamp} | {category}: {idea}"
    append_line(PARKED_FILE, entry)

    log_drift_event(DRIFT_HISTORY, "parked_success", True)

<<<<<<< HEAD
    return _text(msg("parked_add",
        idea=idea, urgency=urgency, category=category,
    ))
=======
    return _text(
        f"🅿️ IDEA PARKED\n\n"
        f"Urgency:  {urgency}\n"
        f"Category: {category}\n\n"
        f"The idea is safe. You can let it go. Return to current task."
    )
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


async def handle_parked_list(args: Dict[str, Any]) -> List[TextContent]:
    if not PARKED_FILE.exists():
        return _text("No items parked yet.")

    filter_type = args.get("filter", "all")

    with open(PARKED_FILE, "r", encoding="utf-8") as f:
        items = f.readlines()

<<<<<<< HEAD
=======
    # Only keep lines that look like parked entries (start with "- [")
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
    entries = [i for i in items if i.startswith("- [")]

    if filter_type == "urgent":
        entries = [i for i in entries if "[BLOCKING]" in i or "[HIGH]" in i]
    elif filter_type == "current_session":
        lock = load_lock()
        if lock is not None:
<<<<<<< HEAD
=======
            # Keep entries timestamped after the current lock was created.
            # Entry format: "- [URGENCY] 2026-03-25T14:30:00 | category: idea"
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
            entries = [
                i for i in entries
                if extract_parked_timestamp(i) >= lock.locked_at
            ]
<<<<<<< HEAD
=======
        # If no lock, current_session is meaningless — return all entries
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b

    return _text("".join(entries) if entries else "No matching items.")


<<<<<<< HEAD
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
=======


async def handle_scope_validate_edit(args: Dict[str, Any]) -> List[TextContent]:
    lock = load_lock()
    if lock is None:
        return _text("⚓ VIOLATION: No active task lock. Cannot validate scope.")

    file_path = args["file_path"]
    if lock.validate_scope(file_path):
        return _text(f"✓ Scope validated: {file_path} is within locked bounds.")

    return _text(
        f"⚓ SCOPE VIOLATION\n\n"
        f"ATTEMPTED: {file_path}\n"
        f"LOCKED SCOPE: {lock.scope_files}\n\n"
        f"This file is outside your current task scope.\n\n"
        f"ACTIONS:\n"
        f"1. Park this edit idea (parked_add)\n"
        f"2. Expand scope (task_lock_create with updated scope)\n"
        f"3. Mark current task done first (task_complete)\n\n"
        f"Current task: {lock.building}"
    )
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


async def handle_task_complete(args: Dict[str, Any]) -> List[TextContent]:
    lock_data = read_json(TASK_LOCK_FILE)
    if lock_data is None:
<<<<<<< HEAD
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
=======
        return _text("⚓ ERROR: No active task to complete.")

    evidence  = args["completion_evidence"]
    exit_cond = lock_data["exit_condition"]

    # Semantic-aware matching: stop-word removal + naive stemming
    # prevents false positives like "test" matching "I tested things"
    match_ratio = score_completion(exit_cond, evidence)

    if match_ratio < 0.5:
        return _text(
            f"⚓ COMPLETION REJECTED\n\n"
            f'Exit condition not satisfied: "{lock_data["exit_condition"]}"\n'
            f"Match ratio: {match_ratio:.0%}\n\n"
            f'Evidence: "{args["completion_evidence"]}"\n\n'
            f"You may be experiencing premature closure (ADHD pattern).\n"
            f"Current task remains LOCKED.\n\n"
            f"Provide evidence that specifically addresses the exit condition."
        )

    # Read rewards config BEFORE deleting the lock file
    rewards = lock_data.get("rewards", {})

    # Celebration (runs before unlink — intentional)
    completion_celebration(lock_data["building"], rewards)

    # Archive to PARKED.md — use append_line's safe mkdir + locking
    completed_section = (
        f"\n\n## COMPLETED: {lock_data['building']}\n"
        f"Completed: {datetime.now().isoformat()}\n"
        f"Evidence: {args['completion_evidence']}\n"
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
    )
    try:
        PARKED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PARKED_FILE, "a", encoding="utf-8") as f:
            f.write(completed_section)
    except OSError:
<<<<<<< HEAD
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
=======
        pass  # Archival is non-critical; don't fail task completion

    # Release lock — missing_ok guards against race if file was already removed
    TASK_LOCK_FILE.unlink(missing_ok=True)

    # Mark for git hook
    EXIT_VALIDATED.touch()

    # Streak
    streak_msg    = increment_streak(STREAK_FILE)
    parked_count  = count_parked()

    return _text(
        f"✓ TASK COMPLETE (Validated)\n"
        f"{streak_msg}\n\n"
        f"Archived: {lock_data['building']}\n"
        f"Match: {match_ratio:.0%} of exit criteria\n\n"
        f"⚓ LOCK RELEASED\n\n"
        f"Next options:\n"
        f"- Create new task lock (task_lock_create)\n"
        f"- Resume a parked item ({parked_count} available)\n"
        f"- Session checkpoint and break (session_checkpoint)"
    )
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


async def handle_session_checkpoint(args: Dict[str, Any]) -> List[TextContent]:
    if not TASK_LOCK_FILE.exists() and not args.get("force"):
<<<<<<< HEAD
        return _text(msg("checkpoint_no_lock"))

    task_data = read_json(TASK_LOCK_FILE)
=======
        return _text("⚓ WARNING: No active task. Pass force=true if intentional.")

    task_data = read_json(TASK_LOCK_FILE)  # None if no lock — that's valid with force
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b

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

<<<<<<< HEAD
=======
    # Git checkpoint commit
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
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
<<<<<<< HEAD
            check=False, timeout=10,
=======
            check=False,
            timeout=10,
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    warning = ""
    if args["emotional_state"] in ("stuck", "frustrated"):
<<<<<<< HEAD
        warning = msg("checkpoint_stuck_warn")

    return _text(msg("checkpoint_saved",
        emotional_state=args["emotional_state"],
        next_action=args["next_micro_action"],
        git_msg=git_msg[:60],
        warning=warning,
    ))
=======
        warning = (
            "\n\n⚠️ MORNING WARNING: You left in a difficult state. "
            "Review the blocker note before resuming."
        )

    return _text(
        f"📋 SESSION ANCHORED\n\n"
        f"State:       {args['emotional_state']}\n"
        f"Next action: {args['next_micro_action']}\n"
        f"Git:         {git_msg[:60]}...\n\n"
        f"SESSION.json and SESSION_LOG.md updated. Work is safe.{warning}\n\n"
        f"To resume: call session_resume when you return."
    )
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


async def handle_session_resume() -> List[TextContent]:
    session = read_json(SESSION_FILE)
    if session is None:
<<<<<<< HEAD
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
=======
        return _text("⚓ No previous session found. Start fresh with task_lock_create.")

    task      = session.get("task") or {}
    emotional = session["emotional_state"]

    body = (
        f"⚓ SESSION RESUME\n\n"
        f"Last active: {session['timestamp'][:16]}\n"
        f"Working on:  {task.get('building', 'Unknown')}\n"
        f"State:       {emotional.upper()}\n"
        f"Next action: {session['next_micro_action']}\n\n"
    )

    if emotional in ("stuck", "frustrated"):
        body += (
            f"⚠️ RESUMPTION ALERT: You left in a difficult state.\n\n"
            f"Blocker was: {session.get('blocker_note') or 'Not recorded'}\n\n"
            f"OPTIONS:\n"
            f'[1] TINY STEP: Attempt "{session["next_micro_action"]}" for 2 minutes\n'
            f"[2] DETOUR: Switch to a parked item (novelty reset)\n"
            f"[3] DEBUG: Analyse blocker before touching code\n"
            f"[4] RESET: Park yesterday's attempt, start fresh"
        )
    else:
        body += (
            f"Ready to resume? Next step: {session['next_micro_action']}\n\n"
            f"Call task_lock_create to re-engage enforcement."
        )

    return _text(body)
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b


async def handle_drift_history_log(args: Dict[str, Any]) -> List[TextContent]:
    log_drift_event(
        DRIFT_HISTORY,
        args.get("drift_type", "unknown"),
        args.get("intervention_successful", True),
    )
    return _text("✓ Drift event logged.")
<<<<<<< HEAD


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
=======
>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b

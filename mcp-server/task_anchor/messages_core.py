"""
messages_core.py — Message templates for lock, drift, parked, and scope.
Single responsibility: message content only. No logic, no I/O.

Each key maps to a dict of {tone: template_string}.
Templates use str.format() placeholders.

Tones: strict | supportive | minimal
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Task lock
# ---------------------------------------------------------------------------

LOCK_ENGAGED = {
    "strict": (
        "⚓ TASK LOCK ENGAGED\n\n"
        "BUILDING: {building}\n"
        "EXIT:     {exit_condition}\n"
        "SCOPE:    {scope}\n"
        "GIT:      {git}\n\n"
        "STATUS: Active enforcement enabled.\n"
        "DRIFT DETECTION: Armed."
    ),
    "supportive": (
        "⚓ Locked in\n\n"
        "Building: {building}\n"
        "Done when: {exit_condition}\n"
        "Scope: {scope}\n"
        "Branch: {git}\n\n"
        "You've got a clear target. Drift detection is watching your back."
    ),
    "minimal": (
        "Locked: {building}\n"
        "Exit: {exit_condition}\n"
        "Scope: {scope}\n"
        "Git: {git}"
    ),
}

NO_LOCK = {
    "strict": (
        "⚓ NO TASK LOCK\n"
        "STATUS: Drift imminent. Create lock immediately.\n"
        "VIOLATION: Cannot proceed with coding tasks."
    ),
    "supportive": (
        "⚓ No task locked yet\n\n"
        "Before we start coding, let's pick one thing to focus on.\n"
        "What are you building? (call task_lock_create)"
    ),
    "minimal": "No active lock. Create one with task_lock_create.",
}

LOCK_STATUS = {
    "strict": (
        "⚓ LOCKED: {building}\n"
        "🎯 EXIT:  {exit_condition}\n"
        "📁 SCOPE: {scope_count} file(s)\n"
        "🕒 Since: {since}"
        "{session_warning}\n\n"
        "Enforcement: ACTIVE"
    ),
    "supportive": (
        "⚓ Working on: {building}\n"
        "Done when: {exit_condition}\n"
        "Scope: {scope_count} file(s) | Since: {since}"
        "{session_warning}"
    ),
    "minimal": (
        "Locked: {building} | Exit: {exit_condition} | {scope_count} files"
        "{session_warning}"
    ),
}

SESSION_WARNING = {
    "strict": (
        "\n⚠️ WARNING: Last session ended in a stuck state. "
        "Review the blocker note before resuming."
    ),
    "supportive": (
        "\n\nHeads up — last session was rough. "
        "Check the blocker note before diving back in; "
        "a fresh angle might help."
    ),
    "minimal": "\n(Stuck last session — review blocker note)",
}


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

DRIFT_DETECTED = {
    "strict": (
        "⚓ DRIFT DETECTED (Score: {score}/{cap})\n\n"
        'DETECTED: "{snippet}"\n\n'
        "ANALYSIS:\n"
        "- Signal match: Probable context switch\n"
        "- Context overlap: {overlap} shared keyword(s)\n"
        "- Suggestion: PARK immediately\n\n"
        "ACTION REQUIRED:\n"
        "Call parked_add to capture this idea, then return to:\n"
        "{context}\n\n"
        "BINARY CHOICE:\n"
        "[1] Park this idea and continue current task\n"
        "[2] Mark current complete and switch (requires validation)"
    ),
    "supportive": (
        "⚓ New thread detected (score: {score}/{cap})\n\n"
        'You said: "{snippet}"\n\n'
        "That sounds like a separate idea — and it might be a good one.\n"
        "Let me save it so you don't lose it.\n\n"
        "Current focus: {context}\n\n"
        "What would you like to do?\n"
        "[1] Park this idea — I'll save it, and we keep going\n"
        "[2] This IS more important — let's switch (finish current first)"
    ),
    "minimal": (
        "Drift (score {score}/{cap}): \"{snippet}\"\n"
        "Overlap: {overlap} | Context: {context}\n"
        "[1] Park  [2] Switch"
    ),
}

DRIFT_CLEAR = {
    "strict": (
        "✓ No drift detected (score: {score}/{cap}). "
        "Proceed with current task."
    ),
    "supportive": "✓ On track (score: {score}/{cap}). Keep going.",
    "minimal": "Clear ({score}/{cap})",
}

DRIFT_FLOW_MODE = {
    "strict": (
        "✓ Flow mode active — drift check skipped. "
        "Expires: {expires}"
    ),
    "supportive": (
        "✓ You're in flow mode — I'll stay out of your way. "
        "Auto-resumes at {expires}."
    ),
    "minimal": "Flow mode ({expires})",
}


# ---------------------------------------------------------------------------
# Parked ideas
# ---------------------------------------------------------------------------

PARKED_ADD = {
    "strict": (
        "🅿️ IDEA PARKED\n\n"
        "Urgency:  {urgency}\n"
        "Category: {category}\n\n"
        "The idea is safe. You can let it go. Return to current task."
    ),
    "supportive": (
        "🅿️ Saved\n\n"
        "'{idea}' is parked ({urgency}, {category}).\n"
        "It's safe — you won't lose it. Back to what we were doing."
    ),
    "minimal": "Parked: {idea} [{urgency}]",
}


# ---------------------------------------------------------------------------
# Scope validation
# ---------------------------------------------------------------------------

SCOPE_NO_LOCK = {
    "strict": "⚓ VIOLATION: No active task lock. Cannot validate scope.",
    "supportive": (
        "⚓ Can't check scope without an active task lock. "
        "Create one first with task_lock_create."
    ),
    "minimal": "No lock — scope check skipped.",
}

SCOPE_PASS = {
    "strict": "✓ Scope validated: {file_path} is within locked bounds.",
    "supportive": "✓ {file_path} — within scope. Go ahead.",
    "minimal": "✓ {file_path}",
}

SCOPE_FAIL = {
    "strict": (
        "⚓ SCOPE VIOLATION\n\n"
        "ATTEMPTED: {file_path}\n"
        "LOCKED SCOPE: {scope}\n\n"
        "This file is outside your current task scope.\n\n"
        "ACTIONS:\n"
        "1. Park this edit idea (parked_add)\n"
        "2. Expand scope (task_lock_create with updated scope)\n"
        "3. Mark current task done first (task_complete)\n\n"
        "Current task: {building}"
    ),
    "supportive": (
        "⚓ That file is outside the current scope\n\n"
        "You're editing: {file_path}\n"
        "Locked scope: {scope}\n\n"
        "Want to:\n"
        "1. Park this idea for later (parked_add)\n"
        "2. Widen the scope (recreate the lock)\n"
        "3. Finish '{building}' first, then tackle this"
    ),
    "minimal": (
        "Out of scope: {file_path}\n"
        "Scope: {scope} | Task: {building}\n"
        "Park / expand scope / finish current first"
    ),
}

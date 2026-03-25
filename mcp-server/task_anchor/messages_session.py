"""
messages_session.py — Message templates for completion, session, flow mode,
and celebration/streak.
Single responsibility: message content only. No logic, no I/O.

Tones: strict | supportive | minimal
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Task completion
# ---------------------------------------------------------------------------

COMPLETION_REJECTED = {
    "strict": (
        "⚓ COMPLETION REJECTED\n\n"
        'Exit condition not satisfied: "{exit_condition}"\n'
        "Match ratio: {ratio}\n\n"
        'Evidence: "{evidence}"\n\n'
        "You may be experiencing premature closure (ADHD pattern).\n"
        "Current task remains LOCKED.\n\n"
        "Provide evidence that specifically addresses the exit condition."
    ),
    "supportive": (
        "⚓ Not quite there yet\n\n"
        'The exit condition is: "{exit_condition}"\n'
        "Match: {ratio}\n\n"
        'Your evidence: "{evidence}"\n\n'
        "I know it feels close — but the exit criteria aren't fully met.\n"
        "Can you describe what specifically satisfies the exit condition?\n"
        "The task stays locked so you don't lose momentum."
    ),
    "minimal": (
        "Incomplete. Exit: \"{exit_condition}\" | Match: {ratio}\n"
        "Provide closer evidence."
    ),
}

COMPLETION_SUCCESS = {
    "strict": (
        "✓ TASK COMPLETE (Validated)\n"
        "{streak}\n\n"
        "Archived: {building}\n"
        "Match: {ratio} of exit criteria\n\n"
        "⚓ LOCK RELEASED\n\n"
        "Next options:\n"
        "- Create new task lock (task_lock_create)\n"
        "- Resume a parked item ({parked_count} available)\n"
        "- Session checkpoint and break (session_checkpoint)"
    ),
    "supportive": (
        "✓ Done! Nice work.\n"
        "{streak}\n\n"
        "Completed: {building}\n"
        "Match: {ratio}\n\n"
        "Lock released. What's next?\n"
        "- Pick another task (task_lock_create)\n"
        "- Revisit a parked idea ({parked_count} saved)\n"
        "- Take a break (session_checkpoint)"
    ),
    "minimal": (
        "✓ Complete: {building} | {ratio} match\n"
        "{streak}\n"
        "Lock released. {parked_count} parked items available."
    ),
}

COMPLETION_NO_LOCK = {
    "strict": "⚓ ERROR: No active task to complete.",
    "supportive": "No task is currently locked — nothing to complete.",
    "minimal": "No active task.",
}


# ---------------------------------------------------------------------------
# Session checkpoint + resume
# ---------------------------------------------------------------------------

CHECKPOINT_NO_LOCK = {
    "strict": "⚓ WARNING: No active task. Pass force=true if intentional.",
    "supportive": (
        "No task is locked right now. "
        "Pass force=true if you still want to checkpoint."
    ),
    "minimal": "No lock. Use force=true to checkpoint anyway.",
}

CHECKPOINT_SAVED = {
    "strict": (
        "📋 SESSION ANCHORED\n\n"
        "State:       {emotional_state}\n"
        "Next action: {next_action}\n"
        "Git:         {git_msg}...\n\n"
        "SESSION.json and SESSION_LOG.md updated. Work is safe."
        "{warning}\n\n"
        "To resume: call session_resume when you return."
    ),
    "supportive": (
        "📋 Session saved\n\n"
        "Feeling: {emotional_state}\n"
        "Next step: {next_action}\n\n"
        "Everything is checkpointed — you can walk away safely."
        "{warning}\n\n"
        "When you're back, call session_resume."
    ),
    "minimal": (
        "Saved. State: {emotional_state} | Next: {next_action}"
        "{warning}"
    ),
}

CHECKPOINT_STUCK_WARNING = {
    "strict": (
        "\n\n⚠️ MORNING WARNING: You left in a difficult state. "
        "Review the blocker note before resuming."
    ),
    "supportive": (
        "\n\nNote to future you: this was a tough spot. "
        "Before jumping back in, read the blocker note — "
        "a fresh perspective usually helps."
    ),
    "minimal": "\n(Stuck — read blocker before resuming)",
}

RESUME_NO_SESSION = {
    "strict": "⚓ No previous session found. Start fresh with task_lock_create.",
    "supportive": (
        "No previous session on file. "
        "Let's start fresh — what would you like to work on?"
    ),
    "minimal": "No session. Use task_lock_create.",
}

RESUME_NORMAL = {
    "strict": (
        "⚓ SESSION RESUME\n\n"
        "Last active: {timestamp}\n"
        "Working on:  {building}\n"
        "State:       {emotional}\n"
        "Next action: {next_action}\n\n"
        "Ready to resume? Next step: {next_action}\n\n"
        "Call task_lock_create to re-engage enforcement."
    ),
    "supportive": (
        "⚓ Welcome back\n\n"
        "Last session: {timestamp}\n"
        "You were working on: {building}\n"
        "You left feeling: {emotional}\n"
        "Next step was: {next_action}\n\n"
        "Ready to pick up where you left off?"
    ),
    "minimal": (
        "Resume: {building} | {timestamp}\n"
        "State: {emotional} | Next: {next_action}"
    ),
}

RESUME_STUCK = {
    "strict": (
        "⚓ SESSION RESUME\n\n"
        "Last active: {timestamp}\n"
        "Working on:  {building}\n"
        "State:       {emotional}\n"
        "Next action: {next_action}\n\n"
        "⚠️ RESUMPTION ALERT: You left in a difficult state.\n\n"
        "Blocker was: {blocker}\n\n"
        "OPTIONS:\n"
        '[1] TINY STEP: Attempt "{next_action}" for 2 minutes\n'
        "[2] DETOUR: Switch to a parked item (novelty reset)\n"
        "[3] DEBUG: Analyse blocker before touching code\n"
        "[4] RESET: Park yesterday's attempt, start fresh"
    ),
    "supportive": (
        "⚓ Welcome back\n\n"
        "Last session: {timestamp}\n"
        "You were working on: {building}\n"
        "You left feeling: {emotional}\n\n"
        "The blocker was: {blocker}\n\n"
        "That was a frustrating spot. Here are some ways back in:\n"
        '[1] Tiny step — just try "{next_action}" for 2 minutes\n'
        "[2] Novelty reset — pick a parked item instead\n"
        "[3] Debug first — think through the blocker before touching code\n"
        "[4] Fresh start — park yesterday's work and begin something new\n\n"
        "No wrong answer. Which feels most doable right now?"
    ),
    "minimal": (
        "Resume: {building} | {timestamp}\n"
        "State: {emotional} | Blocker: {blocker}\n"
        "[1] Tiny step  [2] Switch  [3] Debug  [4] Fresh start"
    ),
}


# ---------------------------------------------------------------------------
# Flow mode
# ---------------------------------------------------------------------------

FLOW_ACTIVATED = {
    "strict": (
        "⚡ FLOW MODE ACTIVE\n\n"
        "Duration: {duration} minutes\n"
        "Expires:  {expires}\n\n"
        "Drift detection SUSPENDED. Scope enforcement remains active.\n"
        "Use flow_mode_deactivate to end early."
    ),
    "supportive": (
        "⚡ Flow mode on\n\n"
        "You've got {duration} minutes of uninterrupted focus.\n"
        "I won't flag drift — just keep building.\n"
        "Scope checks still apply (safety net, not a cage).\n\n"
        "Expires: {expires}"
    ),
    "minimal": "Flow mode: {duration}min until {expires}",
}

FLOW_DEACTIVATED = {
    "strict": "⚡ Flow mode ended. Drift detection RESUMED.",
    "supportive": "⚡ Flow mode off — drift detection is back. Nice session.",
    "minimal": "Flow mode off.",
}

FLOW_EXPIRED = {
    "strict": (
        "⚡ Flow mode EXPIRED. Drift detection resumed.\n"
        "Re-activate with flow_mode_activate if still in flow."
    ),
    "supportive": (
        "⚡ Flow mode expired — checking in.\n"
        "Still in the zone? Call flow_mode_activate to extend.\n"
        "Otherwise, drift detection is back on."
    ),
    "minimal": "Flow expired. Drift detection on.",
}


# ---------------------------------------------------------------------------
# Celebration (streak + completion)
# ---------------------------------------------------------------------------

STREAK_TODAY = {
    "strict": "⚓ ANCHORED 🔒 | {current} day streak (already counted today)",
    "supportive": (
        "⚓ {current}-day streak (already counted today — still impressive)"
    ),
    "minimal": "Streak: {current}d (counted)",
}

STREAK_NEW = {
    "strict": "⚓ ANCHORED {fire} | {current} day streak (Best: {longest})",
    "supportive": "⚓ {fire} {current}-day streak! (Personal best: {longest})",
    "minimal": "Streak: {current}d {fire} (best: {longest})",
}

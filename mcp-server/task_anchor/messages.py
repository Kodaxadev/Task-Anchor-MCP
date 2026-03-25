"""
messages.py — Aggregates all message template modules into a single registry.
Single responsibility: re-export only. No message content defined here.

Split into:
  messages_core.py    — lock, drift, parked, scope
  messages_session.py — completion, session, flow mode, celebration
"""

from __future__ import annotations

from . import messages_core as _core
from . import messages_session as _session


MESSAGES: dict[str, dict[str, str]] = {
    # Core: lock
    "lock_engaged":           _core.LOCK_ENGAGED,
    "no_lock":                _core.NO_LOCK,
    "lock_status":            _core.LOCK_STATUS,
    "session_warning":        _core.SESSION_WARNING,
    # Core: drift
    "drift_detected":         _core.DRIFT_DETECTED,
    "drift_clear":            _core.DRIFT_CLEAR,
    "drift_flow_mode":        _core.DRIFT_FLOW_MODE,
    # Core: parked
    "parked_add":             _core.PARKED_ADD,
    # Core: scope
    "scope_no_lock":          _core.SCOPE_NO_LOCK,
    "scope_pass":             _core.SCOPE_PASS,
    "scope_fail":             _core.SCOPE_FAIL,
    # Session: completion
    "completion_rejected":    _session.COMPLETION_REJECTED,
    "completion_success":     _session.COMPLETION_SUCCESS,
    "completion_no_lock":     _session.COMPLETION_NO_LOCK,
    # Session: checkpoint + resume
    "checkpoint_no_lock":     _session.CHECKPOINT_NO_LOCK,
    "checkpoint_saved":       _session.CHECKPOINT_SAVED,
    "checkpoint_stuck_warn":  _session.CHECKPOINT_STUCK_WARNING,
    "resume_no_session":      _session.RESUME_NO_SESSION,
    "resume_normal":          _session.RESUME_NORMAL,
    "resume_stuck":           _session.RESUME_STUCK,
    # Flow mode
    "flow_activated":         _session.FLOW_ACTIVATED,
    "flow_deactivated":       _session.FLOW_DEACTIVATED,
    "flow_expired":           _session.FLOW_EXPIRED,
    # Celebration
    "streak_today":           _session.STREAK_TODAY,
    "streak_new":             _session.STREAK_NEW,
}

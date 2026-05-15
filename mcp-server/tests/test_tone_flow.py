"""
test_tone_flow.py — Tests for the tone system, flow mode, and message variants.
Validates that all three tones produce distinct output and that flow mode
correctly suspends/resumes drift detection.
"""

import json
import os
import pytest
import importlib
from pathlib import Path

# Fixture `isolated_state` and helper `lock_args` are provided by conftest.py
from conftest import lock_args


# ---------------------------------------------------------------------------
# Tone switching
# ---------------------------------------------------------------------------

class TestToneSystem:

    def test_default_tone_is_supportive(self, isolated_state):
        from task_anchor.tone import get_tone
        assert get_tone() == "supportive"

    def test_set_tone_strict(self, isolated_state):
        from task_anchor.tone import set_tone, get_tone
        set_tone("strict")
        assert get_tone() == "strict"

    def test_set_tone_minimal(self, isolated_state):
        from task_anchor.tone import set_tone, get_tone
        set_tone("minimal")
        assert get_tone() == "minimal"

    def test_set_tone_invalid_raises(self, isolated_state):
        from task_anchor.tone import set_tone
        with pytest.raises(ValueError):
            set_tone("aggressive")

    def test_msg_resolves_correct_tone(self, isolated_state):
        from task_anchor.tone import set_tone, msg
        set_tone("supportive")
        result = msg("no_lock")
        assert "pick one thing to focus on" in result

        set_tone("strict")
        result = msg("no_lock")
        assert "VIOLATION" in result

        set_tone("minimal")
        result = msg("no_lock")
        assert "task_lock_create" in result

    @pytest.mark.asyncio
    async def test_set_tone_handler(self, isolated_state):
        from task_anchor.handlers import handle_set_tone, handle_get_tone
        result = await handle_set_tone({"tone": "minimal"})
        assert "minimal" in result[0].text

        result = await handle_get_tone()
        assert "minimal" in result[0].text

    @pytest.mark.asyncio
    async def test_set_tone_handler_invalid(self, isolated_state):
        from task_anchor.handlers import handle_set_tone
        result = await handle_set_tone({"tone": "angry"})
        assert "Invalid" in result[0].text


# ---------------------------------------------------------------------------
# Supportive tone output
# ---------------------------------------------------------------------------

class TestSupportiveTone:

    @pytest.mark.asyncio
    async def test_lock_create_supportive(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.handlers import handle_task_lock_create
        set_tone("supportive")
        result = await handle_task_lock_create(lock_args())
        assert "Locked in" in result[0].text
        assert "VIOLATION" not in result[0].text

    @pytest.mark.asyncio
    async def test_no_lock_supportive(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.handlers import handle_task_lock_status
        set_tone("supportive")
        result = await handle_task_lock_status()
        assert "pick one thing" in result[0].text
        assert "VIOLATION" not in result[0].text

    @pytest.mark.asyncio
    async def test_completion_rejected_supportive(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.handlers import handle_task_lock_create, handle_task_complete
        set_tone("supportive")
        await handle_task_lock_create(lock_args())
        result = await handle_task_complete({
            "completion_evidence": "I finished stuff"
        })
        assert "Not quite there yet" in result[0].text
        assert "REJECTED" not in result[0].text

    @pytest.mark.asyncio
    async def test_resume_stuck_supportive(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.handlers import handle_task_lock_create
        from task_anchor.handlers_session import handle_session_checkpoint, handle_session_resume
        set_tone("supportive")
        await handle_task_lock_create(lock_args())
        await handle_session_checkpoint({
            "emotional_state": "stuck",
            "next_micro_action": "debug the JWT bug",
            "blocker_note": "jwt.decode throws",
        })
        result = await handle_session_resume()
        # Supportive tone should NOT use "ALERT" or "difficult state"
        assert "Welcome back" in result[0].text
        assert "doable right now" in result[0].text


# ---------------------------------------------------------------------------
# Flow mode
# ---------------------------------------------------------------------------

class TestFlowMode:

    def test_activate_and_check(self, isolated_state):
        from task_anchor.flow import activate, is_active
        minutes, expires = activate(30)
        assert minutes == 30
        active, _ = is_active()
        assert active is True

    def test_deactivate(self, isolated_state):
        from task_anchor.flow import activate, deactivate, is_active
        activate(30)
        deactivate()
        active, _ = is_active()
        assert active is False

    def test_max_duration_capped(self, isolated_state):
        from task_anchor.flow import activate
        minutes, _ = activate(999)
        assert minutes == 120

    @pytest.mark.asyncio
    async def test_drift_detect_skipped_in_flow_mode(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.flow import activate
        from task_anchor.handlers import handle_drift_detect
        set_tone("strict")
        activate(30)
        result = await handle_drift_detect({
            "user_input": "while we're at it let's rewrite everything",
            "current_context": "login endpoint",
        })
        # Should NOT trigger drift — flow mode bypasses it
        assert "DRIFT DETECTED" not in result[0].text
        assert "Flow mode" in result[0].text or "flow mode" in result[0].text

    @pytest.mark.asyncio
    async def test_drift_detect_normal_after_deactivate(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.flow import activate, deactivate
        from task_anchor.handlers import handle_drift_detect
        set_tone("strict")
        activate(30)
        deactivate()
        result = await handle_drift_detect({
            "user_input": "while we're at it let's rewrite everything",
            "current_context": "login endpoint",
        })
        assert "DRIFT DETECTED" in result[0].text

    @pytest.mark.asyncio
    async def test_flow_mode_activate_handler(self, isolated_state):
        from task_anchor.tone import set_tone
        from task_anchor.handlers import handle_flow_mode_activate
        set_tone("supportive")
        result = await handle_flow_mode_activate({"duration_minutes": 45})
        assert "45 minutes" in result[0].text
        assert "cage" not in result[0].text or "not a cage" in result[0].text

    @pytest.mark.asyncio
    async def test_flow_mode_deactivate_handler(self, isolated_state):
        from task_anchor.handlers import handle_flow_mode_activate, handle_flow_mode_deactivate
        await handle_flow_mode_activate({})
        result = await handle_flow_mode_deactivate()
        assert "off" in result[0].text.lower() or "ended" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_drift_detect_flow_expired_notification(self, isolated_state):
        """handle_drift_detect must return a flow-expired notice when the mode
        just auto-expired (is_active returns False, 'expired')."""
        from unittest.mock import patch
        from task_anchor.handlers import handle_drift_detect

        # Simulate the auto-expiry branch: active=False, sentinel='expired'
        with patch("task_anchor.handlers.flow_is_active", return_value=(False, "expired")):
            result = await handle_drift_detect({
                "user_input": "some input",
                "current_context": "login endpoint",
            })

        text = result[0].text
        # The flow_expired message key must produce output (not silently pass through
        # to drift scoring, and not produce a DRIFT DETECTED response)
        assert "DRIFT DETECTED" not in text
        assert "flow" in text.lower() or "expired" in text.lower()

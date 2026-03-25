"""
test_handlers.py — Integration tests for tool handler coroutines.
All state files are redirected to a tmp_path fixture via TASK_ANCHOR_DIR
so tests are fully isolated and never touch real state.
"""

import json
import os
import pytest
import importlib
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixture — isolated state directory per test
# Reloads config + models so TASK_ANCHOR_DIR takes effect cleanly.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Redirect all state file I/O to a fresh temp directory per test."""
    monkeypatch.setenv("TASK_ANCHOR_DIR", str(tmp_path))

<<<<<<< HEAD
    # Force reload of modules that cache paths at import time.
    # Order matters: config → models → messages → tone → helpers/flow → handlers
    import task_anchor.config as cfg
    import task_anchor.models as mdl
    import task_anchor.messages_core as mc
    import task_anchor.messages_session as ms
    import task_anchor.messages as msgs
    import task_anchor.tone as tn
    import task_anchor.flow as flw
    import task_anchor.helpers as hlp
    import task_anchor.streak as strk
    import task_anchor.handlers as hdl
    importlib.reload(cfg)
    importlib.reload(mdl)
    importlib.reload(mc)
    importlib.reload(ms)
    importlib.reload(msgs)
    importlib.reload(tn)
    importlib.reload(flw)
    importlib.reload(hlp)
    importlib.reload(strk)
    importlib.reload(hdl)

    # Set strict tone so existing test assertions (written for strict output) pass.
    tn.set_tone("strict")

=======
    # Force reload of modules that cache paths at import time
    import task_anchor.config as cfg
    import task_anchor.models as mdl
    import task_anchor.helpers as hlp
    import task_anchor.handlers as hdl
    importlib.reload(cfg)
    importlib.reload(mdl)
    importlib.reload(hlp)
    importlib.reload(hdl)

>>>>>>> 3dfce2ba419c32da80299054f4c0620c14fbf49b
    yield tmp_path


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Helper — build a minimal valid lock args dict
# ---------------------------------------------------------------------------

def lock_args(**overrides) -> dict:
    base = dict(
        building="Add login endpoint",
        done_criteria="POST /login returns 200",
        scope_files=["src/auth/"],
        exit_condition="endpoint returns 200 in manual test",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# task_lock_create
# ---------------------------------------------------------------------------

class TestTaskLockCreate:

    @pytest.mark.asyncio
    async def test_creates_lock_file(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create
        from task_anchor.config import TASK_LOCK_FILE
        result = await handle_task_lock_create(lock_args())
        assert TASK_LOCK_FILE.exists()
        assert "TASK LOCK ENGAGED" in result[0].text

    @pytest.mark.asyncio
    async def test_lock_file_contains_correct_data(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create
        from task_anchor.config import TASK_LOCK_FILE
        await handle_task_lock_create(lock_args())
        data = _read(TASK_LOCK_FILE)
        assert data["building"] == "Add login endpoint"
        assert data["status"] == "active"
        assert "rewards" in data


# ---------------------------------------------------------------------------
# task_lock_status
# ---------------------------------------------------------------------------

class TestTaskLockStatus:

    @pytest.mark.asyncio
    async def test_no_lock_returns_violation_message(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_status
        result = await handle_task_lock_status()
        assert "NO TASK LOCK" in result[0].text

    @pytest.mark.asyncio
    async def test_active_lock_returns_status(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create, handle_task_lock_status
        await handle_task_lock_create(lock_args())
        result = await handle_task_lock_status()
        assert "LOCKED" in result[0].text
        assert "Add login endpoint" in result[0].text

    @pytest.mark.asyncio
    async def test_stuck_session_shows_warning(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create, handle_task_lock_status
        from task_anchor.config import SESSION_FILE
        from task_anchor.storage import write_json
        await handle_task_lock_create(lock_args())
        write_json(SESSION_FILE, {"emotional_state": "stuck", "next_micro_action": "fix bug"})
        result = await handle_task_lock_status()
        assert "stuck" in result[0].text.lower() or "WARNING" in result[0].text


# ---------------------------------------------------------------------------
# parked_add + parked_list
# ---------------------------------------------------------------------------

class TestParked:

    @pytest.mark.asyncio
    async def test_parked_add_creates_entry(self, isolated_state):
        from task_anchor.handlers import handle_parked_add
        from task_anchor.config import PARKED_FILE
        result = await handle_parked_add({"idea": "add dark mode", "category": "feature"})
        assert "IDEA PARKED" in result[0].text
        content = PARKED_FILE.read_text()
        assert "dark mode" in content

    @pytest.mark.asyncio
    async def test_parked_add_respects_urgency(self, isolated_state):
        from task_anchor.handlers import handle_parked_add
        from task_anchor.config import PARKED_FILE
        await handle_parked_add({"idea": "critical bug", "category": "bugfix", "urgency": "blocking"})
        assert "[BLOCKING]" in PARKED_FILE.read_text()

    @pytest.mark.asyncio
    async def test_parked_list_returns_items(self, isolated_state):
        from task_anchor.handlers import handle_parked_add, handle_parked_list
        await handle_parked_add({"idea": "add caching", "category": "feature"})
        result = await handle_parked_list({"filter": "all"})
        assert "caching" in result[0].text

    @pytest.mark.asyncio
    async def test_parked_list_urgent_filter(self, isolated_state):
        from task_anchor.handlers import handle_parked_add, handle_parked_list
        await handle_parked_add({"idea": "low priority thing", "category": "feature", "urgency": "low"})
        await handle_parked_add({"idea": "critical fix", "category": "bugfix", "urgency": "blocking"})
        result = await handle_parked_list({"filter": "urgent"})
        assert "critical fix" in result[0].text
        assert "low priority" not in result[0].text

    @pytest.mark.asyncio
    async def test_parked_list_empty(self, isolated_state):
        from task_anchor.handlers import handle_parked_list
        result = await handle_parked_list({})
        assert "No items" in result[0].text


# ---------------------------------------------------------------------------
# scope_validate_edit
# ---------------------------------------------------------------------------

class TestScopeValidate:

    @pytest.mark.asyncio
    async def test_no_lock_returns_violation(self, isolated_state):
        from task_anchor.handlers import handle_scope_validate_edit
        result = await handle_scope_validate_edit({"file_path": "src/auth/login.py"})
        assert "VIOLATION" in result[0].text

    @pytest.mark.asyncio
    async def test_in_scope_file_passes(self, isolated_state, tmp_path):
        from task_anchor.handlers import handle_task_lock_create, handle_scope_validate_edit
        scope = tmp_path / "src" / "auth"
        scope.mkdir(parents=True)
        await handle_task_lock_create(lock_args(scope_files=[str(scope)]))
        result = await handle_scope_validate_edit({"file_path": str(scope / "login.py")})
        assert "validated" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_out_of_scope_file_blocked(self, isolated_state, tmp_path):
        from task_anchor.handlers import handle_task_lock_create, handle_scope_validate_edit
        scope = tmp_path / "src" / "auth"
        scope.mkdir(parents=True)
        outside = tmp_path / "src" / "payments"
        await handle_task_lock_create(lock_args(scope_files=[str(scope)]))
        result = await handle_scope_validate_edit({"file_path": str(outside / "charge.py")})
        assert "SCOPE VIOLATION" in result[0].text


# ---------------------------------------------------------------------------
# task_complete
# ---------------------------------------------------------------------------

class TestTaskComplete:

    @pytest.mark.asyncio
    async def test_no_lock_returns_error(self, isolated_state):
        from task_anchor.handlers import handle_task_complete
        result = await handle_task_complete({"completion_evidence": "done"})
        assert "ERROR" in result[0].text

    @pytest.mark.asyncio
    async def test_weak_evidence_rejected(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create, handle_task_complete
        await handle_task_lock_create(lock_args())
        result = await handle_task_complete({"completion_evidence": "I finished stuff"})
        assert "REJECTED" in result[0].text

    @pytest.mark.asyncio
    async def test_strong_evidence_accepted(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create, handle_task_complete
        from task_anchor.config import TASK_LOCK_FILE
        await handle_task_lock_create(lock_args())
        result = await handle_task_complete({
            "completion_evidence": "endpoint returns 200 in manual test — verified with curl"
        })
        assert "COMPLETE" in result[0].text
        assert not TASK_LOCK_FILE.exists()  # lock must be released

    @pytest.mark.asyncio
    async def test_completion_archives_to_parked(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create, handle_task_complete
        from task_anchor.config import PARKED_FILE
        await handle_task_lock_create(lock_args())
        await handle_task_complete({
            "completion_evidence": "endpoint returns 200 in manual test — all checks pass"
        })
        assert "COMPLETED" in PARKED_FILE.read_text()


# ---------------------------------------------------------------------------
# session_checkpoint + session_resume
# ---------------------------------------------------------------------------

class TestSession:

    @pytest.mark.asyncio
    async def test_checkpoint_writes_session_file(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create, handle_session_checkpoint
        from task_anchor.config import SESSION_FILE
        await handle_task_lock_create(lock_args())
        await handle_session_checkpoint({
            "emotional_state": "satisfied",
            "next_micro_action": "write the tests",
        })
        assert SESSION_FILE.exists()
        data = _read(SESSION_FILE)
        assert data["emotional_state"] == "satisfied"
        assert data["next_micro_action"] == "write the tests"

    @pytest.mark.asyncio
    async def test_checkpoint_no_lock_with_force(self, isolated_state):
        from task_anchor.handlers import handle_session_checkpoint
        result = await handle_session_checkpoint({
            "emotional_state": "tired",
            "next_micro_action": "review parked items",
            "force": True,
        })
        assert "ANCHORED" in result[0].text

    @pytest.mark.asyncio
    async def test_resume_no_session_returns_guidance(self, isolated_state):
        from task_anchor.handlers import handle_session_resume
        result = await handle_session_resume()
        assert "No previous session" in result[0].text

    @pytest.mark.asyncio
    async def test_resume_restores_context(self, isolated_state):
        from task_anchor.handlers import (
            handle_task_lock_create, handle_session_checkpoint, handle_session_resume
        )
        await handle_task_lock_create(lock_args())
        await handle_session_checkpoint({
            "emotional_state": "flow",
            "next_micro_action": "add error handling to login",
        })
        result = await handle_session_resume()
        assert "add error handling to login" in result[0].text

    @pytest.mark.asyncio
    async def test_resume_stuck_state_shows_options(self, isolated_state):
        from task_anchor.handlers import (
            handle_task_lock_create, handle_session_checkpoint, handle_session_resume
        )
        await handle_task_lock_create(lock_args())
        await handle_session_checkpoint({
            "emotional_state": "stuck",
            "next_micro_action": "debug the JWT expiry bug",
            "blocker_note": "jwt.decode throws on refresh tokens",
        })
        result = await handle_session_resume()
        assert "ALERT" in result[0].text or "OPTIONS" in result[0].text


# ---------------------------------------------------------------------------
# drift_history_log
# ---------------------------------------------------------------------------

class TestDriftHistoryLog:

    @pytest.mark.asyncio
    async def test_logs_drift_event(self, isolated_state):
        from task_anchor.handlers import handle_drift_history_log
        from task_anchor.config import DRIFT_HISTORY
        result = await handle_drift_history_log({
            "drift_type": "signal_match",
            "intervention_successful": True,
        })
        assert "logged" in result[0].text.lower()
        data = _read(DRIFT_HISTORY)
        assert data["total_drifts"] >= 1
        assert data["successful_interventions"] >= 1

    @pytest.mark.asyncio
    async def test_logs_failed_intervention(self, isolated_state):
        from task_anchor.handlers import handle_drift_history_log
        from task_anchor.config import DRIFT_HISTORY
        await handle_drift_history_log({
            "drift_type": "scope_creep",
            "intervention_successful": False,
        })
        data = _read(DRIFT_HISTORY)
        assert data["total_drifts"] >= 1
        assert data["successful_interventions"] == 0

    @pytest.mark.asyncio
    async def test_defaults_to_unknown_type(self, isolated_state):
        from task_anchor.handlers import handle_drift_history_log
        result = await handle_drift_history_log({})
        assert "logged" in result[0].text.lower()


# ---------------------------------------------------------------------------
# parked_list — current_session filtering
# ---------------------------------------------------------------------------

class TestParkedCurrentSession:

    @pytest.mark.asyncio
    async def test_current_session_filter_excludes_old_items(self, isolated_state):
        from task_anchor.handlers import handle_parked_add, handle_parked_list
        from task_anchor.config import PARKED_FILE, TASK_LOCK_FILE
        from task_anchor.storage import write_json

        # Simulate an old parked item (timestamp well before the lock)
        PARKED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PARKED_FILE, "w", encoding="utf-8") as f:
            f.write("- [MEDIUM] 2026-01-01T00:00:00 | feature: old idea before lock\n")

        # Create a lock with a known timestamp between old and new items
        from task_anchor.handlers import handle_task_lock_create
        await handle_task_lock_create(lock_args())

        # Add another item AFTER the lock (will have current timestamp)
        await handle_parked_add({"idea": "new idea during lock", "category": "feature"})

        result = await handle_parked_list({"filter": "current_session"})
        assert "new idea during lock" in result[0].text
        assert "old idea before lock" not in result[0].text

    @pytest.mark.asyncio
    async def test_current_session_no_lock_returns_all(self, isolated_state):
        from task_anchor.handlers import handle_parked_add, handle_parked_list
        await handle_parked_add({"idea": "some idea", "category": "feature"})
        result = await handle_parked_list({"filter": "current_session"})
        assert "some idea" in result[0].text


# ---------------------------------------------------------------------------
# completion validation — improved stemming logic
# ---------------------------------------------------------------------------

class TestCompletionValidation:

    @pytest.mark.asyncio
    async def test_false_positive_rejected(self, isolated_state):
        """'I tested things' should NOT match 'endpoint returns 200 in manual test'."""
        from task_anchor.handlers import handle_task_lock_create, handle_task_complete
        await handle_task_lock_create(lock_args())
        result = await handle_task_complete({
            "completion_evidence": "I tested things and it seemed fine"
        })
        assert "REJECTED" in result[0].text

    @pytest.mark.asyncio
    async def test_stemmed_match_accepted(self, isolated_state):
        """'returned 200 from testing' should match 'endpoint returns 200 in manual test'."""
        from task_anchor.handlers import handle_task_lock_create, handle_task_complete
        await handle_task_lock_create(lock_args())
        result = await handle_task_complete({
            "completion_evidence": "endpoint returned 200 when testing manually"
        })
        assert "COMPLETE" in result[0].text

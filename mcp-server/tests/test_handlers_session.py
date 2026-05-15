"""
test_handlers_session.py — Unit tests for handlers_session module.

Two concerns tested here:
1. _run_git_checkpoint: all 4 subprocess outcome branches as a pure unit test
   (no handler call needed, no JSON serialisation involved)
2. Git status propagation: the string returned by _run_git_checkpoint appears
   in the checkpoint response (patched at the function boundary to avoid the
   subprocess.check_output → subprocess.run transitive mock leak)
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from conftest import lock_args


# ---------------------------------------------------------------------------
# _run_git_checkpoint — all subprocess outcome branches (pure unit tests)
# ---------------------------------------------------------------------------

class TestRunGitCheckpoint:
    """Test the git helper directly — no handler invocation, no I/O."""

    def test_returns_committed_on_success(self):
        from task_anchor.handlers_session import _run_git_checkpoint

        success = MagicMock()
        success.returncode = 0

        with patch("task_anchor.handlers_session.subprocess.run", return_value=success):
            status = _run_git_checkpoint("session-anchor: test task")

        assert status.startswith("committed")

    def test_returns_nothing_to_commit_on_exit_1(self):
        from task_anchor.handlers_session import _run_git_checkpoint

        nothing = MagicMock()
        nothing.returncode = 1

        with patch("task_anchor.handlers_session.subprocess.run", return_value=nothing):
            status = _run_git_checkpoint("session-anchor: test task")

        assert status == "skipped — nothing to commit"

    def test_returns_commit_failed_on_nonzero_exit(self):
        from task_anchor.handlers_session import _run_git_checkpoint

        failed = MagicMock()
        failed.returncode = 128

        with patch("task_anchor.handlers_session.subprocess.run", return_value=failed):
            status = _run_git_checkpoint("session-anchor: test task")

        assert "commit failed" in status
        assert "128" in status

    def test_returns_git_not_found_on_file_not_found(self):
        from task_anchor.handlers_session import _run_git_checkpoint

        with patch(
            "task_anchor.handlers_session.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            status = _run_git_checkpoint("session-anchor: test task")

        assert status == "skipped — git not found"

    def test_returns_timeout_on_timeout_expired(self):
        from task_anchor.handlers_session import _run_git_checkpoint

        with patch(
            "task_anchor.handlers_session.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 10),
        ):
            status = _run_git_checkpoint("session-anchor: test task")

        assert status == "skipped — timeout"

    def test_commit_message_truncated_in_committed_status(self):
        from task_anchor.handlers_session import _run_git_checkpoint

        success = MagicMock()
        success.returncode = 0

        # Use a message with a distinctive tail beyond the 50-char cut-off.
        prefix = "a" * 49
        tail = "UNIQUE_TAIL_BEYOND_CUTOFF"
        long_msg = prefix + tail  # 74 chars total

        with patch("task_anchor.handlers_session.subprocess.run", return_value=success):
            status = _run_git_checkpoint(long_msg)

        # First 50 chars (prefix + first char of tail "U") are in the status.
        assert prefix in status
        # The remainder of the tail must not appear.
        assert "NIQUE_TAIL_BEYOND_CUTOFF" not in status


# ---------------------------------------------------------------------------
# Git status propagation — patched at function boundary to avoid transitive
# mock leak (subprocess.check_output calls subprocess.run internally)
# ---------------------------------------------------------------------------

class TestGitStatusInResponse:

    @pytest.mark.asyncio
    async def test_git_status_appears_in_checkpoint_response(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create
        from task_anchor.handlers_session import handle_session_checkpoint

        await handle_task_lock_create(lock_args())

        with patch(
            "task_anchor.handlers_session._run_git_checkpoint",
            return_value="committed — session-anchor: test",
        ):
            result = await handle_session_checkpoint({
                "emotional_state": "flow",
                "next_micro_action": "write the error handler",
            })

        assert "committed" in result[0].text

    @pytest.mark.asyncio
    async def test_skipped_status_propagates(self, isolated_state):
        from task_anchor.handlers import handle_task_lock_create
        from task_anchor.handlers_session import handle_session_checkpoint

        await handle_task_lock_create(lock_args())

        with patch(
            "task_anchor.handlers_session._run_git_checkpoint",
            return_value="skipped — git not found",
        ):
            result = await handle_session_checkpoint({
                "emotional_state": "stuck",
                "next_micro_action": "debug the lock",
            })

        assert "git not found" in result[0].text

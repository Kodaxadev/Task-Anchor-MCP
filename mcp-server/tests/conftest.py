"""
conftest.py — Shared pytest fixtures for the Task Anchor test suite.
"""

import importlib
import pytest


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Redirect all state file I/O to a fresh temp directory per test.

    Reloads config + models so TASK_ANCHOR_DIR takes effect cleanly.
    Order matters: config → models → messages → tone → helpers/flow → handlers → handlers_session
    """
    monkeypatch.setenv("TASK_ANCHOR_DIR", str(tmp_path))

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
    import task_anchor.handlers_session as hdl_session
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
    importlib.reload(hdl_session)

    yield tmp_path


def lock_args(**overrides) -> dict:
    """Build a minimal valid lock args dict for tests."""
    base = dict(
        building="Add login endpoint",
        done_criteria="POST /login returns 200",
        scope_files=["src/auth/"],
        exit_condition="endpoint returns 200 in manual test",
    )
    base.update(overrides)
    return base

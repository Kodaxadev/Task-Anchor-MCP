"""
test_models.py — Unit tests for TaskLock dataclass.
Tests: construction, serialisation, scope validation, from_dict robustness.
"""

import pytest
from task_anchor.models import TaskLock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_lock(**overrides) -> TaskLock:
    defaults = dict(
        building="Add login endpoint",
        done_criteria="POST /login returns 200 with JWT",
        scope_files=["src/auth/"],
        exit_condition="endpoint returns 200 in manual test",
        locked_at="2026-03-25T10:00:00",
    )
    defaults.update(overrides)
    return TaskLock(**defaults)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestTaskLockConstruction:

    def test_defaults_applied(self):
        lock = make_lock()
        assert lock.status == "active"
        assert lock.git_branch is None
        assert lock.emotional_state is None
        assert lock.rewards["visual"] == "minimal"
        assert lock.rewards["sound"] is False

    def test_custom_status(self):
        lock = make_lock(status="suspended")
        assert lock.status == "suspended"

    def test_rewards_not_shared_between_instances(self):
        a = make_lock()
        b = make_lock()
        a.rewards["visual"] = "none"
        assert b.rewards["visual"] == "minimal"  # mutable default must not be shared


# ---------------------------------------------------------------------------
# Serialisation round-trip
# ---------------------------------------------------------------------------

class TestTaskLockSerialisation:

    def test_to_dict_contains_all_fields(self):
        lock = make_lock()
        d = lock.to_dict()
        assert d["building"] == "Add login endpoint"
        assert d["status"] == "active"
        assert "rewards" in d

    def test_from_dict_round_trip(self):
        lock = make_lock(git_branch="feature/login")
        restored = TaskLock.from_dict(lock.to_dict())
        assert restored.building == lock.building
        assert restored.git_branch == "feature/login"
        assert restored.rewards == lock.rewards

    def test_from_dict_strips_unknown_keys(self):
        """Extra keys from future schema additions must not raise TypeError."""
        data = make_lock().to_dict()
        data["future_field"] = "some_value"
        data["another_new_field"] = 42
        lock = TaskLock.from_dict(data)
        assert lock.building == "Add login endpoint"

    def test_from_dict_missing_optional_fields(self):
        """Optional fields absent from old serialised data must use defaults."""
        data = make_lock().to_dict()
        del data["git_branch"]
        del data["emotional_state"]
        lock = TaskLock.from_dict(data)
        assert lock.git_branch is None
        assert lock.emotional_state is None


# ---------------------------------------------------------------------------
# Scope validation
# ---------------------------------------------------------------------------

class TestScopeValidation:

    def test_exact_file_in_scope(self, tmp_path):
        scope = tmp_path / "src" / "auth"
        scope.mkdir(parents=True)
        target = scope / "login.py"
        lock = make_lock(scope_files=[str(scope)])
        assert lock.validate_scope(str(target)) is True

    def test_file_outside_scope(self, tmp_path):
        scope = tmp_path / "src" / "auth"
        scope.mkdir(parents=True)
        outside = tmp_path / "src" / "payments" / "charge.py"
        lock = make_lock(scope_files=[str(scope)])
        assert lock.validate_scope(str(outside)) is False

    def test_scope_is_case_insensitive(self, tmp_path):
        scope = tmp_path / "SRC" / "Auth"
        scope.mkdir(parents=True)
        target = tmp_path / "src" / "auth" / "login.py"
        lock = make_lock(scope_files=[str(scope)])
        assert lock.validate_scope(str(target)) is True

    def test_multiple_scope_files(self, tmp_path):
        auth = tmp_path / "src" / "auth"
        utils = tmp_path / "src" / "utils"
        auth.mkdir(parents=True)
        utils.mkdir(parents=True)
        lock = make_lock(scope_files=[str(auth), str(utils)])
        assert lock.validate_scope(str(utils / "helpers.py")) is True
        assert lock.validate_scope(str(tmp_path / "src" / "payments" / "x.py")) is False

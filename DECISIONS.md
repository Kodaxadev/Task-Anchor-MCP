# Decision Log

Entries required when a change affects >2 files or alters data flow / module boundaries.
Format: Decision → Alternatives → Reasoning → Date.

---

## [2026-05-14] Tech debt fixes: _STOP constant, inline imports, route/tool validation

**Decision:**
1. Hoisted `_STOP` from a set literal rebuilt on every `_meaningful_words` call to a module-level `frozenset` in `drift.py`.
2. Moved four inline imports (`set_tone`, `get_tone`, `VALID_TONES`, `activate`, `deactivate`) from inside handler function bodies to module top-level in `handlers.py`.
3. Added `_assert_routes_match_tools()` to `TaskAnchorServer.__init__` in `server.py`, verified by new tests in `test_server.py`.

**Alternatives considered:**
- Leave inline imports as-is (they work, but hide dependencies from static analysis and linters).
- Put `_STOP` in `models.py` with other constants (reasonable, but drift.py owns the logic that uses it).
- Use `TypedDict` for route/tool validation instead of runtime assertion (requires mypy, no runtime protection).

**Reasoning:** All three were flagged by the code-warden audit as violations of single-concern and performance hygiene rules. None changed observable behavior — purely internal quality improvements. Tests added for all new assertion paths.

**Files affected:** `drift.py`, `handlers.py`, `server.py`, `test_server.py` (new), `test_handlers_session.py` (new)

---

Entries required when a change affects >2 files or alters data flow / module boundaries.
Format: Decision → Alternatives → Reasoning → Date.

---

## [2026-05-14] Fix streak.py MCP protocol violation and validate_scope false positive

**Decision:**
1. Routed all `print()` calls in `completion_celebration` (streak.py) to `sys.stderr`. MCP stdio servers use stdout as the JSON-RPC channel — any non-JSON output there corrupts the protocol.
2. Fixed `validate_scope()` prefix match: appended `os.sep` before `startswith()` so `/project` no longer matches `/project_old/`. Added regression test.

**Alternatives considered:**
- Suppress celebration entirely via env var (already exists as `TASK_ANCHOR_SILENT=1`, but this would make it always silent).
- Remove celebration entirely (disproportionate — the feature has value, just needed the right output stream).
- Use `os.path.normcase()` for cross-platform case sensitivity (correct in theory, but intentional case-insensitivity is a feature for user-typed paths; kept `.lower()`).

**Reasoning:** The stdout bug was a silent protocol violation that only manifests in the live MCP context (not in tests). The prefix bug was a security-adjacent correctness issue — a user could accidentally edit files outside their declared scope. Both warranted immediate fixes.

**Files affected:** `streak.py`, `models.py`, `test_models.py`

---

## [2026-05-14] Split `handlers.py` → `handlers_session.py`

**Decision:** Extracted `handle_session_checkpoint` and `handle_session_resume` into a new `handlers_session.py` module.

**Alternatives considered:**
- Keep everything in `handlers.py` until the 400-line hard limit is hit (deferred the split).
- Split out tone/flow handlers instead (they're smaller, less justification for their own file).
- Split into `handlers_core.py` + `handlers_session.py` + `handlers_misc.py` (over-engineered for current scale).

**Reasoning:** `handlers.py` was at 371 lines — 7 lines from the governance limit. Session lifecycle (checkpoint/resume) is a distinct concern from task enforcement and idea management. The split keeps both files well under 400 lines and makes the module boundary explicit for contributors. The `_run_git_checkpoint` helper was also isolated as a named function, making it independently testable.

**Files affected:** `handlers.py`, `handlers_session.py` (new), `server.py`, `conftest.py`, `test_handlers.py`, `test_tone_flow.py`

---

## [2026-05-14] Add startup integrity check to `messages.py`

**Decision:** Module-level `AssertionError` at import time if any message key is missing a tone variant (`strict`, `supportive`, `minimal`).

**Alternatives considered:**
- Runtime warning instead of hard failure (silent regressions — rejected).
- `TypedDict` enforcement via mypy (requires type-checking pass, not enforced at runtime).
- Test-only assertion in `conftest.py` (wouldn't catch regressions at server startup).

**Reasoning:** The message registry was untyped and the fallback chain (`strict` → raw key) masked missing tones silently. A module-level assertion costs nothing at runtime and catches the error as close to the source as possible — both during testing and on server startup.

**Files affected:** `messages.py`

---

## [2026-05-14] Surface git status in `session_checkpoint` response

**Decision:** `handle_session_checkpoint` now tracks the git result and passes a `git_status` string to the message template instead of silently swallowing failures.

**Alternatives considered:**
- Log to stderr (invisible to the user in MCP context).
- Raise an exception on git failure (git is non-critical; session state was already written).
- Keep silent pass (original behavior — rejected: users had no way to know if state was committed).

**Reasoning:** The session checkpoint's git commit is a best-effort safety net, not a hard requirement. Failing silently was a UX bug: users assumed their work was committed when it may not have been. The fix uses a dedicated `_run_git_checkpoint()` helper that returns a human-readable status string for all four outcomes (committed, nothing to commit, git not found, timeout).

**Files affected:** `handlers_session.py`, `messages_session.py`

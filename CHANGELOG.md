# Changelog

All notable changes to Task Anchor are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-05-15

### Fixed
- `streak.py` — `completion_celebration` was printing to stdout, which is the MCP JSON-RPC channel in stdio servers. All celebration output now routes to stderr
- `validate_scope()` — prefix match allowed `/project_old/file.py` to pass a `/project` scope. Fixed by appending `os.sep` before the `startswith` check; added regression test
- `handlers.py` — `DRIFT_SCORE_CAP` constant was hardcoded as `cap = 10` inside `handle_drift_detect`; now imported from `models.py` so it stays in sync if the threshold changes
- `drift.py` — removed duplicate dead section comment block between `capped_score` and completion validation

### Added
- GitHub Actions CI — runs pytest on Python 3.11, 3.12, and 3.13 on every push and PR; scoped with `permissions: contents: read`
- Flow mode auto-expiry test — `handle_drift_detect`'s `expires == "expired"` branch was previously untested; regression test added to `test_tone_flow.py`
- `handlers_session.py` — session lifecycle handlers split out of `handlers.py`
- Startup integrity check in `messages.py` — raises `AssertionError` at import time if any message key is missing a tone variant
- Git checkpoint status surfaced in `session_checkpoint` response — shows "committed", "skipped — nothing to commit", "skipped — no git repo", or "skipped — timeout" instead of silently passing
- Expanded stop-word list in `drift.py` — reduces false-positive gap-penalty drift on long, on-topic messages with domain-specific vocabulary

### Changed
- `handlers.py` reduced from 371 to ~285 lines by extracting session handlers
- `CHECKPOINT_SAVED` message template updated to show `{git_status}` across all three tones
- CI matrix extended to Python 3.13; `permissions: contents: read` added to workflow
- `__init__.py` version now resolved via `importlib.metadata` — stays in sync with `pyproject.toml` automatically
- `pyproject.toml` gains `[project.urls]` (Repository, Issues, Changelog)
- README: CI badge, updated test count (96 → 108), updated architecture tree
- AGENTS.md updated to reflect full 15-module package structure and all 14 tools (was 8 modules / 9 tools)

---

## [1.1.0] — 2026-04-01

### Added
- Tone system: `strict` / `supportive` (default) / `minimal` — configured via `set_tone` tool
- Flow mode: suspends drift detection for up to 120 minutes (`flow_mode_activate` / `flow_mode_deactivate`)
- Daily streak tracking with completion celebration (`streak.py`)
- `parked_list` urgency and session filters
- `drift_history_log` tool for long-term ADHD pattern analytics
- Cross-platform file locking (`fcntl` on Unix, `msvcrt` on Windows)
- `TASK_ANCHOR_DIR` env-var override for state file location
- 96-test suite with isolated state fixture (no cross-test pollution)

### Changed
- Message templates split into `messages_core.py` and `messages_session.py`
- `session_checkpoint` now scopes git commit to `.claude/skills/task-anchor/` only

### Fixed
- Scope validation now uses case-insensitive prefix matching

---

## [1.0.0] — 2026-03-01

### Added
- 14 MCP tools: `task_lock_create`, `task_lock_status`, `drift_detect`, `scope_validate_edit`, `task_complete`, `parked_add`, `parked_list`, `session_checkpoint`, `session_resume`, `set_tone`, `get_tone`, `flow_mode_activate`, `flow_mode_deactivate`, `drift_history_log`
- Drift scoring engine: 26 weighted signal phrases with whole-word boundary matching
- Context gap penalty for substantive messages with low task-context overlap
- Semantic completion validation: stop-word removal + naive stemming prevents false positives
- Atomic JSON writes via `.tmp` + rename — no state corruption on crash
- `PARKED.md` append-only idea log with urgency and category metadata
- `SESSION_LOG.md` human-readable session history with emotional state capture
- Single-dependency runtime (`mcp~=1.0`)

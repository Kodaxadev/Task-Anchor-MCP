# TASK ANCHOR MCP PROTOCOL

You have access to the Task Anchor MCP server. These tools are MANDATORY, not optional.

## Server Entry Point

The server runs as a Python package. Launch command for Claude Desktop config:

```json
{
  "mcpServers": {
    "task-anchor": {
      "command": "python",
      "args": ["-m", "task_anchor.server"],
      "cwd": "C:/Users/Justi/Downloads/Alpha/TaskAnchor/mcp-server"
    }
  }
}
```

Or if installed via pip (`pip install -e .` from `mcp-server/`):
```json
{ "command": "task-anchor" }
```

State files are written to `.claude/skills/task-anchor/` inside the repo root.
Override location with env var: `TASK_ANCHOR_DIR=C:/custom/path`

## Package Structure

```
mcp-server/
├── pyproject.toml
└── task_anchor/
    ├── config.py           — absolute path resolution (immune to cwd, env-overridable)
    ├── models.py           — TaskLock dataclass, drift signal weights + thresholds
    ├── storage.py          — atomic file I/O, cross-platform locking (fcntl/msvcrt)
    ├── drift.py            — scoring engine, completion validation, history logging
    ├── flow.py             — flow mode activate/deactivate/auto-expire
    ├── tone.py             — tone persistence + message resolver
    ├── messages.py         — message registry (aggregator)
    ├── messages_core.py    — templates: lock, drift, parked, scope
    ├── messages_session.py — templates: completion, session, flow, celebration
    ├── helpers.py          — shared utilities (git branch, load lock, session log)
    ├── streak.py           — daily streak tracking, completion celebration
    ├── tools.py            — MCP tool schema definitions (14 tools)
    ├── handlers.py         — tool handler coroutines
    └── server.py           — MCP wiring, route table, entry point
```

## Available Tools (14)

### Core Enforcement
- `task_lock_create` — Create mandatory task lock with goal, exit condition, file scope
- `task_lock_status` — Check current lock state (call at start of every response)
- `drift_detect` — Score user input for context-switching signals
- `scope_validate_edit` — Verify file is within locked scope before edits
- `task_complete` — Validate completion evidence against exit condition

### Idea Management
- `parked_add` — Save off-topic idea to PARKED.md
- `parked_list` — List parked ideas (filter: all, urgent, current_session)

### Session Continuity
- `session_checkpoint` — Save emotional state, next action, blocker note
- `session_resume` — Restore prior session context with re-entry strategies

### Personalisation
- `set_tone` — Switch voice: strict, supportive (default), or minimal
- `get_tone` — Show current tone setting
- `flow_mode_activate` — Suspend drift detection for hyperfocus (max 120 min)
- `flow_mode_deactivate` — End flow mode early

### Analytics
- `drift_history_log` — Record drift events for pattern analysis

## Absolute Rules

1. You CANNOT write, edit, or create files until `task_lock_status` returns ACTIVE
2. You MUST call `drift_detect` on every user message before responding
3. You MUST call `scope_validate_edit` before modifying any file
4. If `task_lock_status` shows NO TASK LOCK, you MUST refuse to help with code until user creates one

## Enforcement Dialogue

If user tries to skip Task Lock:
> "I cannot help with coding until we lock a task. This prevents ADHD drift. Please describe what you're building so I can call task_lock_create."

If drift_detect returns positive:
> "I've detected potential drift. I'm parking this idea for you (calling parked_add) so it's safe. Now, back to our locked task..."

## Session Protocol

- **Start:** Call `session_resume` to recover prior context. If no session found, call `task_lock_status`.
- **During:** Call `drift_detect` on every user turn. Call `parked_add` for any tangents.
- **End:** `session_checkpoint` is MANDATORY before ending any work session.

# Task Anchor — Agent Instructions

This project includes a Task Anchor MCP server that provides ADHD executive function enforcement. If you have MCP support, connect to it. If not, follow the manual protocol below.

## MCP Server Setup

The server runs as a Python package:

```json
{
  "mcpServers": {
    "task-anchor": {
      "command": "python",
      "args": ["-m", "task_anchor.server"],
      "cwd": "/absolute/path/to/TaskAnchor/mcp-server"
    }
  }
}
```

Or if installed via pip (`pip install -e .` from `mcp-server/`):

```json
{
  "mcpServers": {
    "task-anchor": {
      "command": "task-anchor"
    }
  }
}
```

State files live in `.claude/skills/task-anchor/` inside the repo root.
Override with env var: `TASK_ANCHOR_DIR=/absolute/path/to/state/dir`

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
    ├── messages.py         — message registry (aggregator, integrity-checked at import)
    ├── messages_core.py    — templates: lock, drift, parked, scope
    ├── messages_session.py — templates: completion, session, flow, celebration
    ├── helpers.py          — shared utilities (git branch, load lock, session log)
    ├── streak.py           — daily streak tracking, completion celebration (stderr only)
    ├── tools.py            — MCP tool schema definitions (14 tools)
    ├── handlers.py         — core tool handler coroutines (lock, drift, parked, scope, tone, flow)
    ├── handlers_session.py — session lifecycle handlers (checkpoint, resume)
    └── server.py           — MCP wiring, route table, entry point
```

## Absolute Rules (MCP connected)

1. You CANNOT write, edit, or create files until `task_lock_status` returns ACTIVE
2. You MUST call `drift_detect` on every user message before responding
3. You MUST call `scope_validate_edit` before modifying any file
4. If `task_lock_status` shows NO TASK LOCK, refuse to help with code until the user creates one

## Manual Protocol (no MCP)

If MCP tools are unavailable, enforce these rules through conversation:

**Session start:** Ask "What are we building today?" and require a one-sentence answer with a specific exit condition before proceeding.

**Every message:** Scan for drift signals: "actually", "instead of", "what if we", "while we're at it", "might as well", "different approach", "scrap that". If detected, say: "That sounds like a new idea — let me park it so it's safe. What were we working on?"

**Session end:** Before closing, ask for the next micro-action and emotional state. Write both to a note or comment so the next session can resume cleanly.

## Enforcement Dialogue

If the user tries to skip task lock:
> "I need a task lock before we write any code. What specifically are you building, and what does done look like?"

If drift is detected:
> "I've caught a potential drift. Parking that idea so it's safe — now, back to [current task]."

## Session Protocol

- **Start:** Call `session_resume` (or ask about last session manually)
- **During:** `drift_detect` on every turn, `parked_add` for tangents
- **End:** `session_checkpoint` is mandatory — captures emotional state and next micro-action

## Available Tools (14)

### Core Enforcement

| Tool | Purpose |
|---|---|
| `task_lock_create` | Create task lock with exit criteria |
| `task_lock_status` | Check current lock — call at start of every response |
| `drift_detect` | Analyse input for context-switch signals |
| `parked_add` | Save off-topic idea to PARKED.md |
| `parked_list` | Review parked ideas (filter: all, urgent, current_session) |
| `task_complete` | Validate completion against exit condition |
| `scope_validate_edit` | Enforce file edit boundaries |
| `drift_history_log` | Record drift events for long-term self-monitoring |

### Session Continuity

| Tool | Purpose |
|---|---|
| `session_checkpoint` | Save emotional state, next action, blocker; creates a git commit |
| `session_resume` | Restore prior session context with re-entry strategies |

### Personalisation

| Tool | Purpose |
|---|---|
| `set_tone` | Switch voice: strict, supportive (default), or minimal |
| `get_tone` | Show current tone setting |
| `flow_mode_activate` | Suspend drift detection for hyperfocus (default 30 min, max 120) |
| `flow_mode_deactivate` | End flow mode early and re-enable drift detection |

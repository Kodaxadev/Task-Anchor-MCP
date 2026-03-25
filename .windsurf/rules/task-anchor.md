# Task Anchor Enforcement Protocol

This project includes a Task Anchor MCP server that enforces ADHD executive function constraints. These rules are mandatory.

## MCP Config

Add to Windsurf MCP settings:

```json
{
  "task-anchor": {
    "command": "python",
    "args": ["-m", "task_anchor.server"],
    "cwd": "/absolute/path/to/TaskAnchor/mcp-server"
  }
}
```

## Absolute Rules

- You CANNOT write, edit, or create files until `task_lock_status` returns ACTIVE
- You MUST call `drift_detect` on every user message before responding
- You MUST call `scope_validate_edit` before modifying any file
- If no task lock exists, refuse all coding help until the user creates one with `task_lock_create`

## Enforcement Dialogue

No task lock present:
> "I need a task lock before we write any code. What specifically are you building, and what does done look like?"

Drift detected:
> "I've caught a potential drift. Parking that idea so it's safe — now, back to [current task]."

## Session Protocol

- **Start:** Call `session_resume`. If no session found, call `task_lock_status`.
- **During:** Call `drift_detect` on every user turn. Call `parked_add` for tangents.
- **End:** `session_checkpoint` is MANDATORY before ending any work session.

## Available Tools

`task_lock_create` · `task_lock_status` · `drift_detect` · `parked_add` · `parked_list` · `task_complete` · `session_checkpoint` · `session_resume` · `scope_validate_edit` · `drift_history_log`

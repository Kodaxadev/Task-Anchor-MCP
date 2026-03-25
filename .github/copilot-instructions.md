# Task Anchor Enforcement Protocol

This project includes a Task Anchor MCP server that enforces ADHD executive function constraints. Connect to it via MCP if supported, otherwise follow the manual protocol.

## MCP Config (VS Code settings.json)

```json
{
  "mcp": {
    "servers": {
      "task-anchor": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "task_anchor.server"],
        "cwd": "/absolute/path/to/TaskAnchor/mcp-server"
      }
    }
  }
}
```

## Absolute Rules

- Do not write, edit, or create files until `task_lock_status` returns ACTIVE
- Call `drift_detect` on every user message before responding
- Call `scope_validate_edit` before modifying any file
- If no task lock exists, refuse coding help until the user creates one

## Enforcement Dialogue

No task lock:
> "I need a task lock before we write any code. What specifically are you building, and what does done look like?"

Drift detected:
> "I've caught a potential drift. Parking that idea so it's safe — now, back to [current task]."

## Session Protocol

- **Start:** Call `session_resume`. If no session, call `task_lock_status`.
- **During:** `drift_detect` every turn. `parked_add` for tangents.
- **End:** `session_checkpoint` mandatory before closing session.

## Manual Protocol (if MCP unavailable)

- Require a one-sentence task statement with a specific exit condition before any code
- Scan every message for drift signals: "actually", "instead of", "what if we", "while we're at it", "might as well", "different approach", "scrap that"
- If drift detected, name it explicitly and ask the user to confirm they want to switch tasks or park the idea
- Before ending, capture the next micro-action and emotional state in a comment or note

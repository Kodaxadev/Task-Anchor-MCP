"""
tools.py — MCP Tool schema definitions only.
Single responsibility: declare the 10 tool shapes. Zero handler logic here.
"""

from __future__ import annotations

from mcp.types import Tool


def get_tool_definitions() -> list[Tool]:
    """Returns the full list of Task Anchor MCP tool definitions."""
    return [
        Tool(
            name="task_lock_create",
            description=(
                "Creates a mandatory task lock before any coding. "
                "BLOCKING: Cannot proceed without this."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "building": {
                        "type": "string",
                        "description": "One sentence: What specific feature/bug are you building?",
                    },
                    "done_criteria": {
                        "type": "string",
                        "description": "Observable, testable criteria for completion.",
                    },
                    "scope_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files/folders allowed to touch — enforced by scope_validate_edit.",
                    },
                    "exit_condition": {
                        "type": "string",
                        "description": "The specific micro-step that unlocks the next task.",
                    },
                },
                "required": ["building", "done_criteria", "scope_files", "exit_condition"],
            },
        ),
        Tool(
            name="task_lock_status",
            description=(
                "Gets current task lock status. "
                "Call at the start of every response to display the anchor."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="drift_detect",
            description=(
                "Analyses user input for ADHD drift patterns. "
                "Returns PARK action if drift is detected."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "The raw user message to analyse.",
                    },
                    "current_context": {
                        "type": "string",
                        "description": "What is currently being worked on.",
                    },
                },
                "required": ["user_input", "current_context"],
            },
        ),
        Tool(
            name="parked_add",
            description="Physically parks an idea in PARKED.md. Use when drift_detect returns positive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["feature", "refactor", "research", "bugfix", "tech_debt"],
                        "description": "Type of parked item.",
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["blocking", "high", "medium", "low"],
                        "default": "medium",
                    },
                },
                "required": ["idea", "category"],
            },
        ),
        Tool(
            name="parked_list",
            description="Lists all parked items with optional urgency filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "enum": ["all", "urgent", "current_session"],
                        "default": "all",
                    }
                },
            },
        ),
        Tool(
            name="task_complete",
            description=(
                "Validates completion criteria and unlocks the task. "
                "STRICT: Will reject if criteria are not met."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "completion_evidence": {
                        "type": "string",
                        "description": "Description of what was completed.",
                    },
                    "tests_passing": {"type": "boolean"},
                    "files_modified": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["completion_evidence"],
            },
        ),
        Tool(
            name="session_checkpoint",
            description="Mandatory session-end tool. Writes SESSION.json and creates a git checkpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "emotional_state": {
                        "type": "string",
                        "enum": ["flow", "stuck", "frustrated", "tired", "satisfied"],
                        "description": "Critical for resume protocol.",
                    },
                    "next_micro_action": {
                        "type": "string",
                        "description": "The exact next step (specific, not 'finish the function').",
                    },
                    "blocker_note": {
                        "type": "string",
                        "description": "If stuck, what is the specific blocker?",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Allow checkpoint even without an active task lock.",
                        "default": False,
                    },
                },
                "required": ["emotional_state", "next_micro_action"],
            },
        ),
        Tool(
            name="session_resume",
            description="Retrieves last session context for morning resumption.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="scope_validate_edit",
            description="Call BEFORE editing any file. Returns an error if the file is outside locked scope.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "edit_type": {
                        "type": "string",
                        "enum": ["modify", "create", "delete"],
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="drift_history_log",
            description="Logs a drift event for long-term ADHD self-monitoring pattern analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "drift_type": {"type": "string"},
                    "intervention_successful": {"type": "boolean"},
                },
            },
        ),
        Tool(
            name="set_tone",
            description=(
                "Sets the communication tone for all Task Anchor messages. "
                "Affects how drift, completion, and session messages are worded."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tone": {
                        "type": "string",
                        "enum": ["strict", "supportive", "minimal"],
                        "description": (
                            "strict = enforcement language (VIOLATION, REJECTED). "
                            "supportive = warm coaching voice (default). "
                            "minimal = facts only, shortest output."
                        ),
                    },
                },
                "required": ["tone"],
            },
        ),
        Tool(
            name="get_tone",
            description="Shows the current communication tone setting.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="flow_mode_activate",
            description=(
                "Temporarily suspends drift detection for hyperfocus sessions. "
                "Scope enforcement stays active. Auto-expires after the set duration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Minutes of uninterrupted focus (default 30, max 120).",
                        "default": 30,
                    },
                },
            },
        ),
        Tool(
            name="flow_mode_deactivate",
            description="Ends flow mode early and re-enables drift detection.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

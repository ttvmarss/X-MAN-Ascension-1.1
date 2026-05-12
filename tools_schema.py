"""
Anthropic tool-use schemas for JARVIS actions.
These replace the brittle regex-based [ACTION:...] tags with structured tool calls.
Claude returns a tool_use block; we dispatch it cleanly.
"""

JARVIS_TOOLS = [
    {
        "name": "build_project",
        "description": (
            "Spawn a Claude Code session to build a software project. "
            "Use when the user asks JARVIS to build, create, code, or develop something."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Detailed description of what to build.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Optional short project name (no spaces).",
                },
            },
            "required": ["description"],
        },
    },
    {
        "name": "browse_web",
        "description": "Open a URL or search query in the default browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_or_url": {
                    "type": "string",
                    "description": "Either a full URL (https://...) or a search query.",
                },
            },
            "required": ["query_or_url"],
        },
    },
    {
        "name": "research_topic",
        "description": (
            "Conduct deep research on a topic and produce an HTML report. "
            "Use for questions requiring up-to-date info or detailed analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic."},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "add_task",
        "description": "Add a task or to-do item to JARVIS's tracker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title."},
                "priority": {
                    "type": "integer",
                    "description": "Priority 1 (low) to 5 (urgent). Default 3.",
                    "minimum": 1,
                    "maximum": 5,
                },
                "due_in_hours": {
                    "type": "number",
                    "description": "Optional: hours from now until due.",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "remember",
        "description": (
            "Save a fact, preference, or piece of information for future sessions. "
            "Use when the user says 'remember', 'note that', 'I prefer', etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": "The fact or preference to remember.",
                },
                "category": {
                    "type": "string",
                    "description": "Category: preference, fact, decision, contact.",
                },
            },
            "required": ["fact"],
        },
    },
    {
        "name": "save_note",
        "description": "Save a longer note to the user's notes folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Note content."},
                "title": {"type": "string", "description": "Optional note title."},
            },
            "required": ["content"],
        },
    },
    {
        "name": "make_plan",
        "description": "Generate a multi-step plan for accomplishing a goal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The goal to plan for."},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "open_app_or_url",
        "description": "Open an application by name or a URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "App name (e.g. 'notepad', 'chrome') or full URL.",
                },
            },
            "required": ["target"],
        },
    },
    {
        "name": "connect_to_project",
        "description": (
            "Open a Claude Code session in an existing project directory "
            "to continue work on it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute or ~/-relative path to project.",
                },
            },
            "required": ["project_path"],
        },
    },
]


TOOL_NAMES = {t["name"] for t in JARVIS_TOOLS}

"""Tool registry exposed to Claude via the Anthropic tool-use API."""
from . import filesystem, git_ops, bash_ops, http_ops

# Anthropic tool schemas — sent in every API call
TOOLS = [
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file from the SLH_ECOSYSTEM workspace. Paths must be relative to /workspace. .env files are auto-redacted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path, e.g. 'api/main.py'"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write a UTF-8 text file to the workspace. Creates parent dirs. .env writes are blocked.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files in a workspace directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory relative to /workspace (default '.')"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "bash",
        "description": "Run a shell command. Allowlist: ls, cat, head, tail, grep, find, curl, docker, python, pip, node, npm. Destructive patterns blocked unless ALLOW_DESTRUCTIVE=true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string", "description": "Working dir, relative to /workspace (default root)"},
                "timeout": {"type": "integer", "description": "Seconds, default 60, max 600"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "git",
        "description": "Run a git subcommand: status, log, diff, show, branch, remote, add, commit, pull, push, fetch, rev-parse, config.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subcommand": {"type": "string", "description": "e.g. 'status --short' or 'commit -m ...'"},
                "cwd": {"type": "string", "description": "Repo root relative to /workspace"},
            },
            "required": ["subcommand"],
        },
    },
    {
        "name": "http_get",
        "description": "HTTP GET a URL (used for API health checks). Returns status + body truncated to 4KB.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout": {"type": "integer", "description": "Seconds, default 15"},
            },
            "required": ["url"],
        },
    },
]

# Dispatcher: tool name -> callable.
# filesystem.* and git/bash/http are sync or async — the runner awaits if needed.
HANDLERS = {
    "read_file": filesystem.read_file,
    "write_file": filesystem.write_file,
    "list_dir": filesystem.list_dir,
    "bash": bash_ops.run,
    "git": git_ops.run,
    "http_get": http_ops.get,
}


async def execute(name: str, args: dict) -> str:
    """Dispatch a tool call. Awaits coroutines transparently. Always returns a string."""
    import inspect
    handler = HANDLERS.get(name)
    if not handler:
        return f"[error] unknown tool: {name}"
    try:
        result = handler(**args)
        if inspect.iscoroutine(result):
            result = await result
        return str(result)
    except Exception as e:  # never crash the bot on tool error
        return f"[error] {type(e).__name__}: {e}"

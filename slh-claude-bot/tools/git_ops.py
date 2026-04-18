"""Git operations — thin wrapper over bash with extra safety."""
import os
from pathlib import Path
from . import bash_ops

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()
ALLOW_DESTRUCTIVE = os.getenv("ALLOW_DESTRUCTIVE", "false").lower() == "true"

ALLOWED_GIT_SUBS = (
    "status", "log", "diff", "show", "branch", "remote",
    "add", "commit", "pull", "push",
    "fetch", "rev-parse", "config",
)

FORBIDDEN_SUBSTRINGS = (
    "push --force", "push -f",
    "reset --hard",
    "clean -fd", "clean -fdx",
    "branch -D",
    "filter-branch", "filter-repo",
)


async def run(subcommand: str, cwd: str = "") -> str:
    first = subcommand.strip().split(maxsplit=1)[0] if subcommand.strip() else ""
    if first not in ALLOWED_GIT_SUBS:
        return f"[blocked] git subcommand '{first}' not allowed. Allowed: {', '.join(ALLOWED_GIT_SUBS)}"

    if not ALLOW_DESTRUCTIVE:
        low = subcommand.lower()
        for bad in FORBIDDEN_SUBSTRINGS:
            if bad in low:
                return f"[blocked] destructive git pattern: {bad!r} — set ALLOW_DESTRUCTIVE=true"

    return await bash_ops.run(f"git {subcommand}", cwd=cwd, timeout=120)

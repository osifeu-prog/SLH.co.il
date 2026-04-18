"""Restricted shell executor. Allowlist of safe command prefixes."""
import asyncio
import os
from pathlib import Path

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()
ALLOW_DESTRUCTIVE = os.getenv("ALLOW_DESTRUCTIVE", "false").lower() == "true"

# Prefixes that are always OK
ALLOWED_PREFIXES = (
    "ls", "cat", "head", "tail", "pwd", "echo", "wc",
    "grep", "find", "file", "which",
    "curl", "wget",
    "python", "python3", "pip",
    "docker",
    "node", "npm", "npx",
    "ps",
)

# Substrings that are always BLOCKED (even with ALLOW_DESTRUCTIVE)
HARD_BLOCK = (
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",  # fork bomb
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "chmod 777 /",
)

# Substrings that need ALLOW_DESTRUCTIVE=true
SOFT_BLOCK = (
    "rm -rf",
    "git push --force",
    "git reset --hard",
    "docker system prune",
    "drop database",
    "drop table",
)


def _validate(cmd: str) -> str | None:
    low = cmd.lower()
    for bad in HARD_BLOCK:
        if bad in low:
            return f"[blocked] command contains forbidden pattern: {bad!r}"
    if not ALLOW_DESTRUCTIVE:
        for bad in SOFT_BLOCK:
            if bad in low:
                return f"[blocked] destructive pattern {bad!r} — set ALLOW_DESTRUCTIVE=true to enable"
    first = cmd.strip().split(maxsplit=1)[0] if cmd.strip() else ""
    if not any(first == p or first.startswith(p + " ") or first == p for p in ALLOWED_PREFIXES):
        if ALLOW_DESTRUCTIVE:
            return None  # permissive mode, only HARD_BLOCK applies
        return f"[blocked] command '{first}' not in allowlist. Allowed: {', '.join(ALLOWED_PREFIXES)}"
    return None


async def run(command: str, cwd: str = "", timeout: int = 60) -> str:
    timeout = min(max(timeout, 1), 600)
    err = _validate(command)
    if err:
        return err

    # Resolve cwd inside workspace
    work_dir = (WORKSPACE / cwd).resolve() if cwd else WORKSPACE
    if WORKSPACE not in work_dir.parents and work_dir != WORKSPACE:
        return f"[blocked] cwd outside workspace: {cwd}"

    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=str(work_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return f"[timeout] command exceeded {timeout}s"

    out = stdout.decode("utf-8", errors="replace")
    # Truncate to keep Telegram/Anthropic payloads small
    if len(out) > 8000:
        out = out[:8000] + f"\n... [truncated, total {len(out)} chars]"
    return f"[exit {proc.returncode}]\n{out}" if out.strip() else f"[exit {proc.returncode}] (no output)"

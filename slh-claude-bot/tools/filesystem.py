"""Filesystem tool — read, write, list files under the workspace."""
import os
from pathlib import Path

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()
MAX_FILE_BYTES = 500_000  # 500KB read limit


def _safe_path(rel_path: str) -> Path:
    """Resolve path and verify it stays inside WORKSPACE."""
    candidate = (WORKSPACE / rel_path).resolve()
    if not str(candidate).startswith(str(WORKSPACE)):
        raise PermissionError(f"Path escapes workspace: {rel_path}")
    return candidate


def _mask_secrets(text: str) -> str:
    """Redact obvious token lines for .env-like content."""
    masked = []
    for line in text.splitlines():
        stripped = line.strip()
        if "=" in stripped and any(
            k in stripped.upper()
            for k in ["TOKEN", "SECRET", "KEY", "PASSWORD", "PRIVATE"]
        ):
            name = stripped.split("=", 1)[0]
            masked.append(f"{name}=***REDACTED***")
        else:
            masked.append(line)
    return "\n".join(masked)


def read_file(path: str, mask_secrets: bool = True) -> str:
    p = _safe_path(path)
    if not p.is_file():
        return f"[ERROR] not a file: {path}"
    size = p.stat().st_size
    if size > MAX_FILE_BYTES:
        return f"[ERROR] file too large ({size} bytes, max {MAX_FILE_BYTES})"
    text = p.read_text(encoding="utf-8", errors="replace")
    if mask_secrets and (p.name.startswith(".env") or p.name.endswith(".env")):
        text = _mask_secrets(text)
    return text


def write_file(path: str, content: str) -> str:
    p = _safe_path(path)
    # Block .env writes through the bot (too risky)
    if p.name.startswith(".env") or p.name.endswith(".env"):
        return "[BLOCKED] writes to .env files are disabled. Edit manually on host."
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"[OK] wrote {len(content)} chars to {path}"


def list_dir(path: str = ".") -> str:
    p = _safe_path(path)
    if not p.is_dir():
        return f"[ERROR] not a directory: {path}"
    entries = []
    for child in sorted(p.iterdir()):
        kind = "d" if child.is_dir() else "f"
        size = child.stat().st_size if child.is_file() else 0
        entries.append(f"{kind}\t{size}\t{child.name}")
    return "\n".join(entries) if entries else "(empty)"

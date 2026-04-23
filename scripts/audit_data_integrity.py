# -*- coding: utf-8 -*-
"""
Data Integrity Audit — scan SLH codebase for fake/mock/fallback patterns
that violate CLAUDE.md's "never fake data in production" rule.

Usage:
    python scripts/audit_data_integrity.py
    python scripts/audit_data_integrity.py --json > audit.json
    python scripts/audit_data_integrity.py --severity high

Categories scanned:
    1. JS falsy-fallback with hardcoded numbers  (e.g. `foo || 47`)
    2. HTML hardcoded stat values                (e.g. `<span id="sidebar-online">47</span>`)
    3. Mock markers in strings                   (fake, mock, dummy, placeholder)
    4. Magic numbers in display context          (47, 1000, 9999 + keywords online/users/count)
    5. TODO/FIXME markers referencing real data  ("TODO: connect to API", "FIXME: hardcoded")

Each finding has severity: HIGH | MED | LOW.
HIGH = actively lies to users. MED = may lie under edge cases. LOW = tech debt.

Exit 0 if no HIGH findings; exit 1 if any HIGH.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys

# Force UTF-8 stdout on Windows (avoids cp1252 UnicodeEncodeError on ─ box chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCAN_DIRS = [
    ROOT / "website",
    ROOT / "api",
    ROOT / "routes",
    ROOT / "shared",
]
# Skip heavy/vendor/build
SKIP_DIRS = {"node_modules", ".venv", "venv", ".pio", "__pycache__", ".git", "dist", "build", "backups"}
# Only scan these extensions
EXTS = {".html", ".js", ".py"}


@dataclass
class Finding:
    severity: str         # HIGH | MED | LOW
    category: str
    file: str
    line: int
    snippet: str
    note: str

    def __repr__(self):
        return f"[{self.severity}] {self.file}:{self.line} — {self.note}"


FINDINGS: list[Finding] = []

# ── Rule 1: `|| <digits>` in JS / HTML ─────────────────────────────
# High-risk fallback — JS coerces 0/"" to falsy → fallback fires when real data is 0.
RE_JS_FALLBACK = re.compile(
    r'\b(\w+(?:\.\w+)*|\w+\[[^\]]+\])\s*\|\|\s*(\d{1,5})(?![\d.])'
)

# ── Rule 2: HTML hardcoded stat values ─────────────────────────────
# <span id="...something stat-y..."> <number> </span>
RE_HTML_STAT = re.compile(
    r'<(span|div|strong|b|em|h[1-6])\s+[^>]*id\s*=\s*["\']'
    r'([^"\']*(?:online|members|users|count|total|posts|today)[^"\']*)'
    r'["\'][^>]*>\s*(\d{1,6})\s*</',
    re.IGNORECASE,
)

# ── Rule 3: Mock markers ───────────────────────────────────────────
RE_MOCK = re.compile(r'\b(mock|fake|dummy|placeholder|lorem)\w*', re.IGNORECASE)

# ── Rule 4: TODO/FIXME referencing real data ───────────────────────
RE_TODO = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b[^\n]*\b(real|api|endpoint|live|backend|connect|replace|hardcoded)\b', re.IGNORECASE)

# Contexts where a numeric fallback is LIKELY display (not offset / limit / timeout)
DISPLAY_HINT_RE = re.compile(r'\b(count|online|total|members|users|posts|today|visits|hits|streak|votes|likes|comments)\b', re.IGNORECASE)


def iter_files() -> list[Path]:
    out: list[Path] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_dir():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() not in EXTS:
                continue
            out.append(p)
    return sorted(out)


def scan_file(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # Rule 1: falsy-fallback with number
        for m in RE_JS_FALLBACK.finditer(stripped):
            var, num = m.group(1), m.group(2)
            # skip benign context: limit, offset, timeout, default arg, loop counter
            lower_line = stripped.lower()
            if any(kw in lower_line for kw in ("limit", "offset", "timeout", "delay", "margin", "padding", "width", "height", "fontsize", "zindex", "opacity", "retries", "maxretries")):
                continue
            # Severity heuristic:
            #   `|| 0` or `|| 0.0` — honest (shows 0 when unknown)
            #   `|| <nonzero>` + display hint — HIGH (phantom number)
            #   `|| <nonzero>` elsewhere — MED
            num_int = int(num)
            has_hint = bool(DISPLAY_HINT_RE.search(stripped))
            if num_int == 0:
                sev = "LOW"
                note = f"`{var} || 0` — benign; displays 0 when data missing (matches 0 truthfully)"
            elif has_hint:
                sev = "HIGH"
                note = f"`{var} || {num}` — PHANTOM FALLBACK. When real value is 0, renders {num} as if truth."
            else:
                sev = "MED"
                note = f"`{var} || {num}` — non-zero fallback; verify not user-visible"
            FINDINGS.append(Finding(
                severity=sev, category="JS_FALLBACK",
                file=rel, line=lineno,
                snippet=stripped[:160],
                note=note,
            ))

        # Rule 2: hardcoded stat values in HTML
        if path.suffix.lower() == ".html":
            for m in RE_HTML_STAT.finditer(line):
                _tag, elem_id, num = m.group(1), m.group(2), m.group(3)
                if num in ("0", "00"):
                    continue  # 0 as initial is honest
                FINDINGS.append(Finding(
                    severity="HIGH", category="HTML_HARDCODED_STAT",
                    file=rel, line=lineno,
                    snippet=stripped[:160],
                    note=f"<{_tag} id=\"{elem_id}\"> contains hardcoded {num} — should start as '--' or '0'",
                ))

        # Rule 3: mock markers (context-aware — skip in tests + comments with 'not mock')
        if RE_MOCK.search(stripped) and not any(kw in stripped.lower() for kw in ("not mock", "no mock", "remove mock", "kill mock", "test_", "test.py")):
            if "// " not in stripped and "# " not in stripped:  # not a comment saying "avoid mock"
                # actual mock usage
                FINDINGS.append(Finding(
                    severity="MED", category="MOCK_REFERENCE",
                    file=rel, line=lineno,
                    snippet=stripped[:160],
                    note="contains mock/fake/dummy marker — verify not in production path",
                ))

        # Rule 4: TODO/FIXME around real-data wiring
        if RE_TODO.search(stripped):
            FINDINGS.append(Finding(
                severity="LOW", category="TODO_REAL_DATA",
                file=rel, line=lineno,
                snippet=stripped[:160],
                note="TODO/FIXME mentions real/api/endpoint — incomplete wiring",
            ))


def print_human(severity_filter: str | None) -> None:
    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    sorted_findings = sorted(FINDINGS, key=lambda f: (order.get(f.severity, 9), f.category, f.file, f.line))

    if severity_filter:
        sorted_findings = [f for f in sorted_findings if f.severity == severity_filter.upper()]

    if not sorted_findings:
        print("✓ No data-integrity violations found.")
        return

    by_sev: dict[str, list[Finding]] = {}
    for f in sorted_findings:
        by_sev.setdefault(f.severity, []).append(f)

    print(f"\n=== Data Integrity Audit ({len(sorted_findings)} findings) ===\n")
    for sev in ("HIGH", "MED", "LOW"):
        fs = by_sev.get(sev, [])
        if not fs:
            continue
        print(f"── {sev} ({len(fs)}) ──")
        for f in fs:
            print(f"  {f.file}:{f.line}  [{f.category}]")
            print(f"      {f.snippet[:140]}")
            print(f"      → {f.note}")
            print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human output")
    parser.add_argument("--severity", choices=["HIGH", "MED", "LOW"], help="filter to severity")
    args = parser.parse_args()

    files = iter_files()
    for p in files:
        scan_file(p)

    if args.json:
        print(json.dumps([asdict(f) for f in FINDINGS], ensure_ascii=False, indent=2))
    else:
        print_human(args.severity)
        print(f"Scanned {len(files)} files. Total findings: {len(FINDINGS)}.")

    high_count = sum(1 for f in FINDINGS if f.severity == "HIGH")
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

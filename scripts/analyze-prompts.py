#!/usr/bin/env python3
"""
SLH Prompt Analyzer
====================
Scans the codebase for AI prompts and reports:
  - Token count per prompt
  - Estimated monthly cost
  - Cache savings potential
  - De-noising opportunities

Usage:
    python scripts/analyze-prompts.py                  # all prompts
    python scripts/analyze-prompts.py --top 5          # only top 5 by cost
    python scripts/analyze-prompts.py --denoise        # also write cleaned versions
    python scripts/analyze-prompts.py --json           # JSON output for tooling

Author: Claude (Cowork mode, 2026-04-27)
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path

# Make shared/ importable regardless of where this script is run from
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "shared"))
from ai_optimizer import analyze_prompt, denoise_prompt, estimate_tokens

# Patterns that look like a prompt assignment
PROMPT_PATTERNS = [
    re.compile(r'(\w*(?:SYSTEM_)?PROMPT\w*)\s*=\s*"""(.*?)"""', re.DOTALL),
    re.compile(r"(\w*(?:SYSTEM_)?PROMPT\w*)\s*=\s*'''(.*?)'''", re.DOTALL),
]

# Estimated daily call volumes (rough — adjust per-bot from real metrics)
DAILY_CALLS = {
    "claude_client.py":     200,   # main executor — high frequency
    "free_ai_client.py":    150,
    "ai_chat.py":           500,   # public AI chat — highest
    "ai_cmd.py":            80,
    "DEFAULT":              50,
}

SKIP_DIRS = {".git", "node_modules", ".venv", "venv_shared", ".pio",
             "libdeps", "backups", "_backups", "_restore", "archive",
             "__pycache__", ".snapshots"}

def walk_python_files(root: Path):
    for p in root.rglob("*.py"):
        # Skip junk
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p

def find_prompts_in_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    found = []
    for pat in PROMPT_PATTERNS:
        for m in pat.finditer(content):
            name, text = m.group(1), m.group(2).strip()
            if len(text) < 80:  # Skip tiny strings
                continue
            found.append((name, text))
    return found

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=0, help="Only show top N by cost")
    parser.add_argument("--denoise", action="store_true", help="Write *.denoised.py files")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--root", default=str(ROOT), help="Root to scan")
    args = parser.parse_args()

    root = Path(args.root)
    results = []

    for path in walk_python_files(root):
        prompts = find_prompts_in_file(path)
        for name, text in prompts:
            calls = DAILY_CALLS.get(path.name, DAILY_CALLS["DEFAULT"])
            analysis = analyze_prompt(name, text, calls_per_day=calls)
            analysis["file"] = str(path.relative_to(root))
            results.append(analysis)

    # Sort by current monthly cost (descending)
    results.sort(key=lambda r: r["monthly_cost_ils"]["current_no_optimization"], reverse=True)

    if args.top > 0:
        results = results[:args.top]

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # Pretty text report
    print()
    print("═" * 78)
    print(f"  SLH Prompt Analyzer — {len(results)} prompts found")
    print("═" * 78)
    print()

    total_current = sum(r["monthly_cost_ils"]["current_no_optimization"] for r in results)
    total_optimized = sum(r["monthly_cost_ils"]["with_denoising_and_caching"] for r in results)
    total_savings = total_current - total_optimized

    print(f"  TOTAL monthly cost (no optimization): ₪{total_current:.2f}")
    print(f"  TOTAL monthly cost (with denoise+cache): ₪{total_optimized:.2f}")
    print(f"  TOTAL savings: ₪{total_savings:.2f}/month ({total_savings/max(total_current,0.01)*100:.1f}%)")
    print()
    print("─" * 78)
    print(f"  {'NAME':<25} {'TOKENS':>8} {'CALLS':>8} {'CURRENT':>10} {'OPTIMIZED':>10} {'SAVE':>8}")
    print("─" * 78)
    for r in results:
        print(f"  {r['name'][:24]:<25} "
              f"{r['tokens']['original']:>8} "
              f"{r['calls_per_day']:>8} "
              f"₪{r['monthly_cost_ils']['current_no_optimization']:>8.2f} "
              f"₪{r['monthly_cost_ils']['with_denoising_and_caching']:>8.2f} "
              f"{r['monthly_cost_ils']['savings_pct']:>6.0f}%")
    print("─" * 78)
    print()
    print("  Top 3 detail:")
    for r in results[:3]:
        print(f"\n  📊 {r['name']}  ({r['file']})")
        print(f"     Tokens: {r['tokens']['original']} → {r['tokens']['denoised']} "
              f"(saved {r['tokens']['tokens_saved_by_denoising']}, "
              f"{r['tokens']['pct_saved_by_denoising']}%)")
        print(f"     Cost:   ₪{r['monthly_cost_ils']['current_no_optimization']}/mo "
              f"→ ₪{r['monthly_cost_ils']['with_denoising_and_caching']}/mo "
              f"(saves ₪{r['monthly_cost_ils']['savings_vs_current']})")
    print()

if __name__ == "__main__":
    main()

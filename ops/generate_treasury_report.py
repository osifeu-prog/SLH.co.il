#!/usr/bin/env python3
"""
Monthly Treasury Report Generator
==================================

Hits /api/treasury/health, formats the R/P/W/Buffer/Breakeven snapshot into
a human-readable Hebrew markdown report, and saves it to
ops/treasury-reports/YYYY-MM.md.

Usage:
    python ops/generate_treasury_report.py            # current month
    python ops/generate_treasury_report.py --month 2026-04
    python ops/generate_treasury_report.py --api https://slh-api-production.up.railway.app

Schedule it:
    # Run on the 1st of each month at 09:00 (cron on Railway or local Windows Task Scheduler)
    0 9 1 * * cd /app && python ops/generate_treasury_report.py

Output goes to ops/treasury-reports/ which is a regular git-tracked directory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_API = os.getenv("TREASURY_REPORT_API", "https://slh-api-production.up.railway.app")
REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "ops" / "treasury-reports"


def fetch_health(api_base: str) -> dict:
    url = api_base.rstrip("/") + "/api/treasury/health"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        print(f"ERROR: API returned {e.code}: {e.reason}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"ERROR: could not reach API at {url}: {e.reason}", file=sys.stderr)
        raise


def ils(value) -> str:
    """Format a number as an ILS amount (e.g. 1,234.56)."""
    if value is None:
        return "—"
    try:
        v = float(value)
        return f"{v:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return str(value)


STATUS_LABEL_HE = {
    "pre_revenue": "🔵 Pre-revenue (טרום-הכנסות)",
    "healthy": "🟢 Healthy (בריא)",
    "caution": "🟡 Caution (זהירות)",
    "undercollateralized": "🔴 Undercollateralized (חשיפה)",
}

TIER_LABEL_HE = {
    "survival": "Survival (1,000 ₪/חודש)",
    "sustainable": "Sustainable (5,000 ₪/חודש)",
    "thriving": "Thriving (20,000 ₪/חודש)",
    "above_thriving": "מעל Thriving — איזור הצמיחה",
}


def build_report(data: dict, month_label: str) -> str:
    as_of = data.get("as_of", "")
    status = data.get("status") or {}
    R = data.get("R_revenue") or {}
    P = data.get("P_contingent_obligations") or {}
    W = data.get("W_outflows") or {}
    B = data.get("buffer") or {}
    BE = data.get("breakeven") or {}
    rates = data.get("rates_ils") or {}
    notes = data.get("notes") or []

    status_line = STATUS_LABEL_HE.get(status.get("code"), status.get("code", "—"))
    coverage = status.get("coverage_ratio")
    coverage_str = "—" if coverage is None else f"{coverage * 100:.2f}%"

    next_tier = BE.get("next_milestone")
    next_tier_label = TIER_LABEL_HE.get(next_tier, next_tier or "—")
    gap = BE.get("gap_to_next_ils")
    gap_str = "הושג ✓" if not gap or gap <= 0 else f"{ils(gap)} ₪"

    survival_pct = (BE.get("progress_pct") or {}).get("survival")
    sustain_pct = (BE.get("progress_pct") or {}).get("sustainable")
    thriving_pct = (BE.get("progress_pct") or {}).get("thriving")

    burns_lines = []
    for tok, d in (W.get("burns_by_token") or {}).items():
        burns_lines.append(f"  - **{tok}**: {ils(d.get('amount'))} ({d.get('count', 0)} events)")
    burns_block = "\n".join(burns_lines) if burns_lines else "  - (אין burns עדיין)"

    rates_lines = [f"  - {k}: {ils(v)} ₪" for k, v in rates.items()]
    rates_block = "\n".join(rates_lines)

    notes_block = "\n".join(f"- {n}" for n in notes) or "- —"

    report = f"""# Treasury Report · {month_label}

*נוצר אוטומטית מ-/api/treasury/health · snapshot at `{as_of}`*

---

## 🎯 Bottom Line

**סטטוס:** {status_line}
**יחס כיסוי (Buffer / P):** {coverage_str}
**יעד הבא:** {next_tier_label}
**פער ליעד:** {gap_str}

---

## 💰 R — Revenue In

| תקופה | סכום (₪) |
|---|---|
| היום | {ils(R.get('ils_today'))} |
| 7 ימים | {ils(R.get('ils_7d'))} |
| 30 ימים | **{ils(R.get('ils_30d'))}** |
| מתחילת הדרך | {ils(R.get('ils_lifetime'))} |

### Breakdown לפי מטבע (lifetime)
"""

    lifetime_by_cur = (R.get("by_currency_period") or {}).get("lifetime") or {}
    if lifetime_by_cur:
        for cur, d in lifetime_by_cur.items():
            report += f"- **{cur}**: {ils(d.get('amount'))} ({d.get('count', 0)} עסקאות)\n"
    else:
        report += "- (אין עסקאות עדיין)\n"

    report += f"""
---

## 📏 P — Contingent Obligations

| רכיב | ערך |
|---|---|
| סה״כ התחייבות מותנית (₪) | {ils(P.get('ils_total'))} |
| ZVK פעיל (יחידות) | {ils(P.get('zvk_outstanding_units'))} |
| ZVK שווי ₪ | {ils(P.get('zvk_contingent_ils'))} |
| התחייבות Buyback עתידית | {ils(P.get('upcoming_slh_buyback_ils'))} |
| שיעור Buyback | {pct(float(P.get('buyback_rate', 0)) * 100)} |

---

## 💸 W — Executed Outflows

| רכיב | ערך |
|---|---|
| סה״כ תזרים יוצא (₪) | {ils(W.get('ils_total'))} |
| Buybacks שבוצעו (₪) | {ils(W.get('buybacks_executed_ils'))} |
| SLH נרכש | {ils(W.get('buybacks_slh_bought'))} |
| מספר Buybacks | {W.get('buybacks_count', 0)} |
| Burns (שווי ₪) | {ils(W.get('burns_ils_equiv'))} |

### Burns by Token
{burns_block}

---

## 🛡️ Buffer

| רכיב | ערך |
|---|---|
| סה״כ Buffer (₪) | **{ils(B.get('ils_total'))}** |
| AIC Reserve (USD) | {ils(B.get('reserve_usd'))} |
| Net Treasury (₪) | {ils(B.get('net_treasury_ils'))} |

---

## 🎯 Break-Even Progress (Level 5 Model)

| יעד | סף (₪/חודש) | התקדמות |
|---|---|---|
| Survival | 1,000 | **{pct(survival_pct)}** |
| Sustainable | 5,000 | {pct(sustain_pct)} |
| Thriving | 20,000 | {pct(thriving_pct)} |

**R_30d נוכחי:** {ils(BE.get('current_r_ils_30d'))} ₪

---

## 💱 שערי המרה שומשו

{rates_block}

---

## 📝 הערות מה-API

{notes_block}

---

## 🔍 מסקנות + המלצות

"""

    # Heuristic commentary
    survival_pct_val = float(survival_pct or 0)
    if survival_pct_val < 10:
        report += (
            "- **מצב:** עמוק ב-pre-revenue. R_30d מתחת ל-10% מ-Survival. פעולה דרושה: הפעלת Ambassador/VIP.\n"
            "- **המלצה:** קמפיין גיוס של 3 שגרירים + 10 מנויי VIP בחודש הבא (= ~1,985 ₪/חודש → 198% Survival).\n"
        )
    elif survival_pct_val < 50:
        report += (
            "- **מצב:** זנב של pre-revenue — יש תחילת תנועה אבל עדיין רחוק מ-Survival.\n"
            "- **המלצה:** ממש בזמן להכפיל את ערוצי ה-recurring (VIP / Ambassador).\n"
        )
    elif survival_pct_val < 100:
        report += (
            "- **מצב:** קרוב ל-Survival. כל שגריר/VIP נוסף בחודש הזה חוצה את הסף.\n"
            "- **המלצה:** דחוף את הכפתורים האחרונים — אפילו פגישת מכירה אחת מוצלחת תדחוף אותך ל-Green.\n"
        )
    else:
        report += (
            "- **מצב:** מעל Survival — המערכת מרוויחה.\n"
            "- **המלצה:** התמקד ב-Sustainable (5,000 ₪/חודש). זה מממן שיווק + עתודה.\n"
        )

    report += f"""
---

*דוח זה נוצר באמצעות `ops/generate_treasury_report.py` מ-{DEFAULT_API}*
*לצפייה חיה: [/treasury-health.html](https://slh-nft.com/treasury-health.html)*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate monthly treasury report from /api/treasury/health")
    parser.add_argument("--api", default=DEFAULT_API, help="API base URL")
    parser.add_argument("--month", help="Label for the report (defaults to current month YYYY-MM)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing to file")
    args = parser.parse_args()

    month_label = args.month or datetime.now(timezone.utc).strftime("%Y-%m")

    print(f"Fetching snapshot from {args.api}/api/treasury/health ...", file=sys.stderr)
    data = fetch_health(args.api)

    print("Building report...", file=sys.stderr)
    report = build_report(data, month_label)

    if args.stdout:
        print(report)
        return

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / f"{month_label}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"✓ Saved: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

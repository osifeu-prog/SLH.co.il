# -*- coding: utf-8 -*-
"""
Generate personalized Telegram outreach messages for SLH community members.

Output: ops/OUTREACH_BATCH_<DATE>.md — a markdown document with one ready-to-send
message per user. Osif copy-pastes each from his personal Telegram account
(NOT via bot — bot DMs had 0% engagement overnight).

Usage:
    python scripts/bulk_personalized_messages.py
    # → writes ops/OUTREACH_BATCH_20260422.md
    # → prints preview

Segmentation is manual (by user_id in USERS below) because 20 users don't
warrant clustering. Adjust segment / template / name for each user directly.
"""
from __future__ import annotations

import io
import sys
from datetime import date
from pathlib import Path

# Force UTF-8 stdout on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ops" / f"OUTREACH_BATCH_{date.today().strftime('%Y%m%d')}.md"

BASE = "https://slh-nft.com"


# ══════════════════════════════════════════════════════════════════════
# User roster (manually curated — edit here)
# segment: 'investor' | 'creator' | 'ambassador' | 'community' | 'intro'
# skip=True if already messaged directly today
# ══════════════════════════════════════════════════════════════════════
USERS = [
    # --- Already messaged directly today (skip) ---
    {"uid": 590733872,  "name": "יערה",     "handle": "@Yaara_Kaiser",    "segment": "creator",    "skip": True,  "note": "WhatsApp personal sent today — awaiting reply"},
    # --- Priority: re-engage (yesterday's bot-DM was ignored) ---
    {"uid": 1185887485, "name": "צביקה",    "handle": "@tzvika21truestory","segment": "investor",  "skip": False, "note": "Co-founder. Promoted to founders in b48a1b1 (pending deploy)."},
    {"uid": 8088324234, "name": "אליעזר",   "handle": "@P22PPPPPP",       "segment": "ambassador", "skip": False, "note": "130 investors. CRM Phase 0 waits his CSV."},
    {"uid": 480100522,  "name": "זוהר",     "handle": "@Zoharot",         "segment": "community",  "skip": False, "note": "Community leader, asked good QA questions in the past."},
    {"uid": 920721513,  "name": "Rami",    "handle": "@rami1864",        "segment": "intro",      "skip": False, "note": "Unknown — intro conversation first."},
    # --- Not yet messaged ---
    {"uid": 1518680802, "name": "Idan",    "handle": "@Allonethought",   "segment": "community",  "skip": False, "note": "IT background per memory — potential contributor."},
    {"uid": 6192197452, "name": "Halit",   "handle": None,               "segment": "community",  "skip": False, "note": "Unknown but is_registered=TRUE."},
    {"uid": 6526198118, "name": "יהונתן",  "handle": None,               "segment": "community",  "skip": False, "note": "Unknown but is_registered=TRUE."},
    {"uid": 8265956478, "name": "Shachar", "handle": "@ShacharDs",       "segment": "community",  "skip": False, "note": "Unknown but is_registered=TRUE."},
    # --- Bounced on bot DM (needs phone/WhatsApp, not included here) ---
    {"uid": 7940057720, "name": "יהב",     "handle": "@Yahav_anter",     "segment": "community",  "skip": True,  "note": "Bot DM bounced — needs to /start @SLH_AIR_bot first. Skip bulk, handle via phone."},
]


# ══════════════════════════════════════════════════════════════════════
# Templates per segment
# Placeholders: {name}, {link}
# ══════════════════════════════════════════════════════════════════════
TEMPLATES = {

    "investor": {
        "page": "/invest-preview.html",
        "campaign": "investor-outreach",
        "body": (
            "היי {name} 👋\n\n"
            "שבת שלום / שבוע טוב (לפי מתי שאתה קורא).\n\n"
            "רציתי לעדכן אותך ישירות — SLH Spark עברה בלילה האחרון סבב פיתוח משמעותי. "
            "עכשיו יש לנו תשתית מלאה (113+ endpoints, 25 בוטים, פלטפורמה יציבה), "
            "ואני בונה שכבת Partnership Preview לאנשים שאני רוצה שיהיו חלק מההחלטות הגדולות.\n\n"
            "קראתי כאן בצורה מתומצתת מה יש ולאן זה הולך:\n"
            "{link}\n\n"
            "זה לא סבב השקעה — זה שלב של דיאלוג. 20-30 דק' זום בנוחות שלך, אני שומע "
            "מה מעניין אותך ואיפה אתה רואה fit. אם יש — נמשיך. אם לא — נשמור קשר.\n\n"
            "אין דחיפות. תענה כשנוח לך. 🙏"
        ),
    },

    "ambassador": {
        "page": "/pay-creator-package.html",
        "campaign": "ambassador-outreach",
        "body": (
            "היי {name} 👋\n\n"
            "שבת שלום.\n\n"
            "אני זוכר שסיפרת על 130 המשקיעים שאתה מלווה. בניתי עבורך משהו — כלי CRM "
            "מלא שמשולב באקוסיסטם של SLH, בעברית, חינם בשלב הזה.\n\n"
            "איך זה עובד:\n"
            "1. שם אחד בוט טלגרם אישי שלך (@SLH_Eliezer_bot או שם אחר שתבחר)\n"
            "2. מייבאים את 130 האנשים מאקסל/WhatsApp export לפי הפורמט שאתה כבר עובד איתו\n"
            "3. אתה מקבל ניהול pipeline מלא: lead → qualified → committed → funded\n"
            "4. חיפוש מהיר, התראות \"מי לא דיברתי איתו 30+ יום\", dashboard אישי\n\n"
            "הרחבה מלאה + טופס ראשוני כאן:\n"
            "{link}\n\n"
            "כרגע אין תנועת כסף דרך SLH (דורש ישות משפטית נפרדת — עובדים על זה), "
            "אז זה CRM טהור. ברגע שהרגולציה משחררת — נוסיף את שכבת ההשקעה.\n\n"
            "מה שאני צריך ממך ברגע זה: אקסל של ה-130 (או דוגמה). אני מייבא אוטומטית.\n\n"
            "מתי נוח לך לדבר? 🙏"
        ),
    },

    "creator": {
        "page": "/pay-creator-package.html",
        "campaign": "creator-outreach",
        "body": (
            "היי {name} 👋\n\n"
            "(Already handled via WhatsApp — skip in bulk send)"
        ),
    },

    "community": {
        "page": "/community-beta.html",
        "campaign": "community-outreach",
        "body": (
            "היי {name} 👋\n\n"
            "שבת שלום!\n\n"
            "אוסיף פה — רציתי להודות לך על שהרשמת ל-SLH Spark. אנחנו ב-Alpha מלאה עכשיו, "
            "וכל פידבק משנה את המערכת ברמה יומית.\n\n"
            "הכנתי דף ייעודי שמסביר מה ה-Alpha Community מקבל:\n"
            "• Dashboard אישי\n"
            "• 500 ZVK על חתימה ראשונה\n"
            "• גישה מוקדמת לכל הפיצ'רים\n"
            "• קבוצת טלגרם סגורה עם הצוות\n\n"
            "{link}\n\n"
            "אין תשלום, אין התחייבות. רק שיחה ישירה על מה מעניין אותך במערכת ומה היית "
            "רוצה לראות שונה.\n\n"
            "אם לא רלוונטי בכלל — בלי דחיפות, פשוט תגיד ואל תרגיש צורך לענות. 🙏"
        ),
    },

    "intro": {
        "page": "/community-beta.html",
        "campaign": "intro-outreach",
        "body": (
            "היי 👋\n\n"
            "אוסיף מ-SLH Spark — ראיתי שנרשמת למערכת אצלנו ורציתי להכיר אותך לפני שאני "
            "מציע משהו קונקרטי.\n\n"
            "שלוש שאלות קצרות (ענה בעצלנות, בלי לחץ):\n"
            "1. מה הביא אותך אלינו?\n"
            "2. במה אתה מתעסק ביומיום?\n"
            "3. איפה חסר לך כלי / תמיכה / מערכת שהיית רוצה?\n\n"
            "אחרי שאני שומע ממך, אני מתאים משהו — אם זה Alpha Community בסיסי, שותפות "
            "טכנית, או רק להישאר בקשר.\n\n"
            "{link} — דף Alpha אם תרצה לראות מה זה לפני.\n\n"
            "🙏"
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════
def build_link(u: dict) -> str:
    tpl = TEMPLATES[u["segment"]]
    qs = f"?uid={u['uid']}&src=tg&campaign={tpl['campaign']}"
    return f"{BASE}{tpl['page']}{qs}"


def render_message(u: dict) -> str:
    tpl = TEMPLATES[u["segment"]]
    link = build_link(u)
    return tpl["body"].format(name=u["name"], link=link)


def main() -> int:
    today = date.today().strftime("%Y-%m-%d")
    lines: list[str] = []
    lines.append(f"# SLH Outreach Batch — {today}\n")
    lines.append(f"**Source roster:** 10 users (reg=TRUE in prod, from `/api/ops/reality`).")
    lines.append(f"**Channel:** Telegram personal from **@osifeu_prog** (NOT bot — bot DMs had 0% engagement overnight).")
    lines.append(f"**Action:** For each user below, open their Telegram chat (by @handle or via search by name), copy the message block, and send.")
    lines.append(f"**Attribution:** Every link carries `?uid=<id>&src=tg&campaign=<seg>` — track in `visitor_events`.\n")

    lines.append("---\n")

    active = [u for u in USERS if not u.get("skip")]
    skipped = [u for u in USERS if u.get("skip")]

    lines.append(f"## 📤 To send: {len(active)} users\n")

    for i, u in enumerate(active, 1):
        handle = u["handle"] or "(לחפש בטלגרם לפי user_id / name)"
        lines.append(f"### {i}. {u['name']} — `{u['uid']}` — {handle}")
        lines.append(f"**Segment:** `{u['segment']}`  |  **Note:** {u['note']}\n")
        lines.append(f"**Tracked link:** <{build_link(u)}>\n")
        lines.append("**Message to copy:**")
        lines.append("```")
        lines.append(render_message(u))
        lines.append("```\n")
        lines.append("---\n")

    if skipped:
        lines.append(f"## ⏸ Skipped: {len(skipped)} users\n")
        for u in skipped:
            lines.append(f"- **{u['name']}** (`{u['uid']}` / {u['handle'] or '—'}) — {u['note']}")
        lines.append("")

    lines.append("## 📊 Expected metrics")
    lines.append("")
    lines.append("Based on last night's 6 bot DMs (0/6 engagement in 16h), personal messages from Osif should see:")
    lines.append("")
    lines.append("- View rate: 70-100% (they see your name)")
    lines.append("- Link-click rate: 30-50%")
    lines.append("- Response rate: 15-30% (3-4 replies from 9 sends)")
    lines.append("- Conversion to Zoom: 5-15% (1-2 Zoom calls)")
    lines.append("")
    lines.append("Watch `visitor_events` for `{campaign}_view`, `_cta_whatsapp`, `_cta_questions` hits.\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written: {OUT}")
    print(f"  {len(active)} messages ready to copy-paste")
    print(f"  {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())

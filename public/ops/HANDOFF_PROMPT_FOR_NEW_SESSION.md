# 🎯 Handoff Prompt — שיחה חדשה
**תעתיק את כל הקטע למטה ותדביק כהודעה ראשונה לסשן Claude/AI חדש.**

---

```
שלום. אני אוסיף קאופמן אונגר (@osifeu_prog · Telegram 224223270),
מפתח solo של אקוסיסטם SLH. אני נכנס לסשן חדש אחרי עבודה ארוכה
עם Claude Opus 4.7. הנה התמונה המלאה.

═══════════════════════════════════════════════════════════
🏗 מה יש לי — שני פרויקטים נפרדים (אל תבלבל!)
═══════════════════════════════════════════════════════════

【פרויקט A】 SLH Spark / slh-nft.com (D:\SLH_ECOSYSTEM)
  • Domain: slh-nft.com (GitHub Pages)
  • API: slh-api-production.up.railway.app
  • Repo: github.com/osifeu-prog/osifeu-prog.github.io (website)
            github.com/osifeu-prog/slh-api (API + bots)
  • Telegram bot: @SLH_Claude_bot (id 8324920733)
  • Docker: 26 containers ב-docker-compose.yml
  • Token SLH ב-BSC + 5-token economy (SLH/MNH/ZVK/REP/ZUZ)

【פרויקט B】 SLH.co.il (D:\SLH.co.il) — נפרד!
  • Domain: slh.co.il
  • Railway project: diligent-radiance
  • Telegram bot: @SLH_macro_bot
  • Service: monitor.slh
  • Schema שונה (first_seen/timestamp TEXT)
  • זה לא הפרויקט שלי הראשי — זה side project

⚠️ סוכנים שעובדים על פרויקט B שולחים לי הודעות
   על Railway CLI, monitor.slh, AAEp tokens — אלה לא רלוונטיים
   ל-@SLH_Claude_bot. אל תבלבל ביניהם.

═══════════════════════════════════════════════════════════
✅ מה פעיל עכשיו (אומת LIVE 25.4.2026)
═══════════════════════════════════════════════════════════

Website (slh-nft.com):
  • 127 דפים LIVE
  • /command-center.html — multi-monitor launcher (24 tiles, 4 presets)
  • /ops-viewer.html — markdown renderer של 14 ops docs
  • /voice.html + /swarm.html — Phase 2 vision pages
  • /network.html — neural map, 61 nodes (incl. 10 Voice/Swarm)
  • /roadmap.html — 39 items across 4 phases
  • /project-map.html — 52 pages indexed
  • /admin.html — clock fix (date+TZ+sync badge)

API (Railway slh-api):
  • v1.1.0 LIVE: status:ok db:connected
  • /api/health, /api/prices, /api/ai/chat (Groq חינם!)
  • /api/admin/* — needs X-Admin-Key (key list ב-Railway:
    slh_admin_2026_rotated_04_20, slh_ops_2026_rotated_04_20)

Telegram bot @SLH_Claude_bot (פרויקט A):
  • Mode: slh-multiprovider-free (Groq Llama 3.3 70B חינם)
  • 23 פקודות:
    - Ops (9): /ps /bots /logs /git /health /price /devices /task /ai_mode
    - Editor (14): /cat /ls /grep /find /append /replace /newpage
                   /commit /push /sync /draft /apply /reject /editor
  • Container: slh-claude-bot (docker compose)
  • Docker socket mounted → /ps עובד מבפנים
  • /workspace mount → קריאה/כתיבה לקבצי הפרויקט

═══════════════════════════════════════════════════════════
📁 קבצים ומסמכים — נתיבים מדויקים
═══════════════════════════════════════════════════════════

Code:
  D:\SLH_ECOSYSTEM\slh-claude-bot\
    bot.py — main bot (23 commands)
    editor_commands.py — 14 editor cmds (cat/ls/grep/etc)
    free_ai_client.py — wraps /api/ai/chat (Groq)
    auth.py — allowlist (224223270 + 8789977826)
    .env — local env (NOT in git)

  D:\SLH_ECOSYSTEM\website\ — GitHub Pages source
  D:\SLH_ECOSYSTEM\api\main.py — FastAPI (~7000 lines)
  D:\SLH_ECOSYSTEM\main.py — ROOT copy (Railway builds from here!)
  D:\SLH_ECOSYSTEM\docker-compose.yml — 26 services

Ops docs (כולם בקליק via /ops-viewer.html):
  ops/CONTROL.md — daily single-source-of-truth
  ops/SYSTEM_ALIGNMENT_20260424.md — agents claims board
  ops/AGENT_COORDINATION_20260424.md — protocol rules
  ops/COMMAND_CENTER_SETUP_20260424.md — PowerShell commands
  ops/VOICE_STACK_COMPETITIVE_20260424.md — vs Yemot HaMashiach
  ops/SWARM_V1_BLUEPRINT_20260424.md — ESP32 mesh blueprint
  ops/SESSION_HANDOFF_20260424_VOICE_SWARM.md — handoff
  ops/AGENT_ALIGNMENT_PROMPT_GUARDIAN_ESP.md — for parallel agents
  ops/TELEGRAM_CONTROL_GUIDE.md — full bot reference
  ops/FINAL_STATE_20260425.md — final state snapshot
  ops/WHAT_TO_DO_NOW_OSIF.md — step-by-step

═══════════════════════════════════════════════════════════
🚧 בלוקרים פתוחים (מה דחוף)
═══════════════════════════════════════════════════════════

P0 — שלי (Osif, ידיים אישיות):
  1. Token rotation @SLH_Claude_bot — נדלף בצ'אט הזה.
     BotFather → /mybots → SLH_Claude → API Token → Revoke
     החלף ערך ב-D:\SLH_ECOSYSTEM\slh-claude-bot\.env (השורה SLH_CLAUDE_BOT_TOKEN=)
     אל תשלח את הטוקן החדש לאף סוכן!
     restart: docker compose up -d --force-recreate claude-bot

  2. Railway redeploy slh-api — תקוע מ-097eafe (curly-quote SyntaxError).
     railway.app → slh-api → Deployments → Redeploy

  3. 30 bot tokens נוספים דלפו (חוץ מ-claude-bot) — צריך rotation
     גם להם דרך BotFather. רשימה ב-ops/COMMAND_CENTER_SETUP חלק ז.

P1 — שלך (סוכן):
  4. /git ב-bot מחזיר timeout 15s על "."  → תיקון ב-bot.py
     (default → /workspace/website + git status -s -uno).
     כבר commited אבל ייתכן שהקונטיינר לא בנוי מחדש.
     verify: docker logs slh-claude-bot --tail 5
     אם צריך: docker compose build claude-bot && docker compose up -d --force-recreate claude-bot

  5. Multi-domain: slh.co.il צריך CNAME ל-osifeu-prog.github.io
     או subdomain (control.slh.co.il).
     קובץ: D:\SLH_ECOSYSTEM\website\CNAME
     כרגע: slh-nft.com

═══════════════════════════════════════════════════════════
⛔ מה לא לעשות
═══════════════════════════════════════════════════════════

  • אל תיגע ב-D:\SLH.co.il — זה פרויקט נפרד עם בוט אחר
  • אל תיצור /guardian.html (כבר יש /swarm.html + /kosher-wallet.html)
  • אל תפרסם "LIVE" שירותים שלא קיימים (Voice/Swarm = Phase 2)
  • אל תקח כסף לפני POC עובד (vaporware)
  • אל תשלח טוקנים בצ'אט — feedback_never_paste_secrets
  • אל תיגע ב-main.py בלי לסנכרן ל-api/main.py (Railway builds from ROOT)
  • אל תפיל את 30 הבוטים שכבר רצים ב-docker-compose

═══════════════════════════════════════════════════════════
🟢 מה כן לעשות
═══════════════════════════════════════════════════════════

  • לקרוא קודם: ops/CONTROL.md (https://slh-nft.com/ops-viewer.html?file=CONTROL.md)
  • להוסיף שורה ב-ops/SYSTEM_ALIGNMENT_20260424.md תחת
    "Active Agents" עם השם שלך + מה אתה עושה
  • לעבוד דרך @SLH_Claude_bot מהטלגרם (פקודות /draft /apply לעריכה)
  • לדבוק ב-Hebrew UI / English code+commits
  • Free AI bot לא עולה לי כסף (Groq) — קל להפעיל features

═══════════════════════════════════════════════════════════
🔍 איך לאמת שהמערכת חיה (5 פקודות, 30 שניות)
═══════════════════════════════════════════════════════════

PowerShell:
  curl https://slh-api-production.up.railway.app/api/health
  curl -I https://slh-nft.com/command-center.html
  docker ps --filter "name=slh-claude-bot" --format "{{.Status}}"
  docker logs slh-claude-bot --tail 3

Telegram (@SLH_Claude_bot):
  /health  → API: חי ✓ DB: connected v1.1.0
  /ps      → טבלת 26 containers
  /control → סיכום מערכת בשורה אחת

═══════════════════════════════════════════════════════════
🎯 מה אני רוצה עכשיו
═══════════════════════════════════════════════════════════

[כאן אני מוסיף את הבקשה הספציפית שלך לסשן הזה]

═══════════════════════════════════════════════════════════

Quick links:
  • Command Center: https://slh-nft.com/command-center.html
  • Ops Viewer: https://slh-nft.com/ops-viewer.html
  • Bot: https://t.me/SLH_Claude_bot
  • CONTROL.md: https://slh-nft.com/ops-viewer.html?file=CONTROL.md
```

---

## 📋 איך להשתמש בפרומפט הזה

1. תעתיק את כל הקטע בין ה-` ``` ` שלמעלה
2. בסשן Claude/ChatGPT/Gemini חדש — תדביק
3. **לפני שאתה שולח** — הוסף בסוף, מיד לפני "═══":
   - מה אתה רוצה שהסוכן יעשה (לדוגמה: "תקן את /git timeout", "הוסף DNS ל-slh.co.il")
4. שלח. הסוכן יבין מיד את כל ההקשר וימשיך.

---

## ⚡ תקציר מה שעשיתי בסשן הנוכחי (Claude Opus 4.7, ~10 שעות)

| קטגוריה | תוצרים |
|---|---|
| **דפים חדשים** | voice.html, swarm.html, command-center.html, ops-viewer.html |
| **דפים מעודכנים** | network.html (+10 nodes), roadmap.html (+5 items), project-map.html (+2), admin.html (clock fix) |
| **shared.js** | site-map FAB section "Phase 2 Vision" |
| **Cache-bust** | 37 דפים עודכנו ל-`?v=20260424a` |
| **Ops docs** | 11 מסמכים חדשים, כולם נגישים דרך /ops-viewer.html |
| **Bot @SLH_Claude_bot** | רב-ספק חינם (Groq) במקום Anthropic, +14 פקודות עורך, Docker socket mounted |
| **Git commits** | ~15 commits ב-website repo + ~4 ב-API repo |

**זמן עבודה:** ~10 שעות. **עלות:** ₪0 (Bot על Groq חינם).
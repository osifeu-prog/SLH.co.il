"""
Seed the Mission Control tasks table from KNOWN_ISSUES + DROP_OFF handoffs.

Run once after Railway deploys the new /api/admin/tasks endpoints.

Usage:
  set ADMIN_API_KEY=slh_admin_2026_rotated_04_20
  set API_BASE=https://slh-api-production.up.railway.app
  python scripts/seed_tasks_from_handoff.py

Or for local:
  set API_BASE=http://localhost:8000
  python scripts/seed_tasks_from_handoff.py
"""
import json
import os
import sys
import urllib.request

API_BASE = os.getenv("API_BASE", "https://slh-api-production.up.railway.app")


# Tasks extracted from ops/KNOWN_ISSUES.md + TEAM_HANDOFF_20260424/*.md
# Each maps source → deduplicated so re-runs are safe.
TASKS = [
    # ─── DROP_OSIF_OWNER (P0 user-actions) ────────────────────
    {
        "title": "Railway Redeploy — 5 commits stuck",
        "description": "5 commits (b48a1b1 → e49a57b) on origin/master but API serves v1.1.0. Root: commit 097eafe introduced curly-quote SyntaxErrors, build pipeline paused. Click Redeploy on commit 6892556.",
        "category": "owner", "priority": "P0", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "DROP_OSIF_OWNER #1", "estimated_minutes": 1,
    },
    {
        "title": "Push website/miniapp + marketplace.html + team.html",
        "description": "4 files in website/miniapp/ + marketplace.html + team.html exist locally but never pushed. Currently all 404 on slh-nft.com.",
        "category": "owner", "priority": "P0", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "DROP_OSIF_OWNER #2", "estimated_minutes": 5,
    },
    {
        "title": "Fix global git config — 'Your Name' authorship",
        "description": "Commits 097eafe + a94e682 attributed to 'Your Name <your.email@example.com>'. Run: git config --global user.name/email.",
        "category": "owner", "priority": "P0", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "DROP_OSIF_OWNER #3", "estimated_minutes": 1,
    },
    {
        "title": "Rotate 10 leaked secrets",
        "description": "OpenAI, Gemini, Groq, BSCScan, 2 bot tokens, JWT, ENCRYPTION, ADMIN_API_KEYS, ADMIN_BROADCAST_KEY leaked in chat transcripts. Rotate all; update .env + Railway env vars.",
        "category": "security", "priority": "P0", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "KNOWN_ISSUES K-1", "estimated_minutes": 20,
    },
    {
        "title": "Set ANTHROPIC_API_KEY for @SLH_Claude_bot",
        "description": "slh-claude-bot/.env line 8 empty. Free-text handler fails until set. /health /price /devices /task work fine.",
        "category": "owner", "priority": "P1", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "KNOWN_ISSUES K-9", "estimated_minutes": 2,
    },
    {
        "title": "SQL review for user 8789977826 — ₪147 refund or upgrade",
        "description": "User paid ₪49×4=196, 0 licenses. Fix pushed b4da6b1. 3 duplicate payments flagged refund_status=pending_review. Decide: refund ₪147 or upgrade to VIP for +₪353.",
        "category": "owner", "priority": "P1", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "DROP_OSIF_OWNER #6", "estimated_minutes": 10,
    },

    # ─── DROP_INFRA_DEVOPS ────────────────────────────────────
    {
        "title": "Docker rebuild 9 Phase 0B bots",
        "description": "academia, airdrop, admin, expertnet, guardian, ledger, nfty, osif-shop, social bots — code committed but containers running stale image.",
        "category": "infra", "priority": "P0", "status": "open",
        "assignee_name": "Idan", "source": "KNOWN_ISSUES K-7", "estimated_minutes": 30,
    },
    {
        "title": "Fix ledger-bot TOKEN vs BOT_TOKEN crash loop",
        "description": "RestartCount=169. docker-compose.yml sets TOKEN=${BOT_TOKEN} but service reads LEDGER_BOT_TOKEN. Update compose or fix code fallback.",
        "category": "infra", "priority": "P0", "status": "open",
        "assignee_name": "Idan", "source": "KNOWN_ISSUES K-8", "estimated_minutes": 5,
    },
    {
        "title": "Flash ESP32 firmware v3 to physical device",
        "description": "Firmware v3 built at device-registry/esp32-cyd-work/firmware/slh-device-v3/. pio run -t upload --upload-port COM5. Then register device via /api/device/register.",
        "category": "infra", "priority": "P2", "status": "open",
        "assignee_name": "Idan", "source": "DROP_INFRA #3", "estimated_minutes": 15,
    },
    {
        "title": "Schedule daily_backtest.py on Railway cron",
        "description": "/api/performance returns available:false because CSV not generated on Railway. Add Railway Cron: '0 */6 * * *' running daily_backtest.py.",
        "category": "infra", "priority": "P1", "status": "open",
        "assignee_name": "Idan", "source": "KNOWN_ISSUES K-14", "estimated_minutes": 10,
    },
    {
        "title": "Set BSCSCAN_API_KEY on Railway",
        "description": "/network.html + /blockchain.html show 0 holders, 0 tx without the key. After rotation (DROP_OSIF #4 item 4), Idan adds to Railway Variables.",
        "category": "infra", "priority": "P2", "status": "blocked",
        "blocker": "Waiting for Osif to rotate BSCScan key first",
        "assignee_name": "Idan", "source": "KNOWN_ISSUES K-17", "estimated_minutes": 2,
    },

    # ─── Code fixes (P0) ──────────────────────────────────────
    {
        "title": "3 admin endpoints bypass _require_admin()",
        "description": "main.py:957 (registration approve), 2344 (beta coupon), 4782 (marketplace approve) use admin_secret body field instead of X-Admin-Key header.",
        "category": "security", "priority": "P0", "status": "open",
        "source": "KNOWN_ISSUES K-2", "estimated_minutes": 30,
    },
    {
        "title": "_dev_code leaks in /api/device/verify",
        "description": "main.py:10498-10499 returns dev_code field for QR-pairing UX. In prod this exposes the pairing code. Gate behind DEV=true env or remove.",
        "category": "security", "priority": "P0", "status": "open",
        "source": "KNOWN_ISSUES K-3", "estimated_minutes": 10,
    },
    {
        "title": "/api/events/public returns event_log_unavailable",
        "description": "event_log table missing. Create with schema matching api/telegram_gateway._audit writer.",
        "category": "code", "priority": "P0", "status": "open",
        "source": "KNOWN_ISSUES K-4", "estimated_minutes": 20,
    },
    {
        "title": "initShared() never fires on 121 HTML pages",
        "description": "website/js/shared.js:1091 defines initShared() but no DOMContentLoaded call. Fix: add DOMContentLoaded listener at bottom of shared.js.",
        "category": "code", "priority": "P0", "status": "open",
        "source": "KNOWN_ISSUES K-5", "estimated_minutes": 10,
    },

    # ─── P1 Code ─────────────────────────────────────────────
    {
        "title": "buy.html hardcodes tokenPrices={SLH:122,...}",
        "description": "Line 333-334 + '|| 122' fallback. Quoted buy amounts use stale price. Hydrate from /api/prices + new /api/wallet/price?tokens=SLH,MNH,ZVK endpoint.",
        "category": "code", "priority": "P1", "status": "open",
        "source": "KNOWN_ISSUES K-11", "estimated_minutes": 45,
    },
    {
        "title": "Activity feed emoji corruption (ðŸ¤, ðŸ'Ž)",
        "description": "UTF-8 read as Latin-1 somewhere between DB → API JSON. Trace emoji insertion path in main.py transaction endpoints.",
        "category": "code", "priority": "P1", "status": "open",
        "source": "KNOWN_ISSUES K-12", "estimated_minutes": 30,
    },
    {
        "title": "14 HTML files × 27 '65% APY' leftovers from Dynamic Yield pivot",
        "description": "JS layer fixed (commit 7ff9db1) but HTML still has hardcoded. Bulk replace '65%' → 'Dynamic'.",
        "category": "code", "priority": "P1", "status": "open",
        "source": "KNOWN_ISSUES K-13", "estimated_minutes": 20,
    },
    {
        "title": "Deposits schema drift — token vs currency, confirmed_at vs created_at",
        "description": "Root of 8789977826 payment bug. Patched in b4da6b1 but schema not unified. DB migration to pick one set of columns everywhere.",
        "category": "code", "priority": "P1", "status": "open",
        "source": "KNOWN_ISSUES K-15", "estimated_minutes": 90,
    },
    {
        "title": "Academia VIP ₪99 (HTML) vs ₪549 (API) mismatch",
        "description": "/academia.html shows ₪99, /api/academia/courses returns ₪549. Decide canonical + align.",
        "category": "code", "priority": "P1", "status": "open",
        "source": "KNOWN_ISSUES K-10", "estimated_minutes": 15,
    },
    {
        "title": "admin.html uses localStorage for admin password (XSS risk)",
        "description": "Migrate admin.html to Mini App + Gateway auth per TELEGRAM_FIRST_MIGRATION_PLAN phase 2.",
        "category": "security", "priority": "P1", "status": "open",
        "source": "KNOWN_ISSUES K-16", "estimated_minutes": 180,
    },

    # ─── P2 Tech debt ────────────────────────────────────────
    {
        "title": "94 console.log calls in production website JS",
        "description": "Remove or gate behind debug flag before prod launch.",
        "category": "code", "priority": "P2", "status": "open",
        "source": "KNOWN_ISSUES K-18", "estimated_minutes": 30,
    },
    {
        "title": "Delete stale deploy artifacts",
        "description": "website/rotate.html, test-bots.html, ops-report-20260411.html shouldn't be public. Per TELEGRAM_FIRST_MIGRATION_PLAN deletes list.",
        "category": "code", "priority": "P2", "status": "open",
        "source": "KNOWN_ISSUES K-19", "estimated_minutes": 5,
    },
    {
        "title": "Zero automated tests on 114 API endpoints",
        "description": "Scaffold pytest with 20 tests covering payment + admin critical paths.",
        "category": "qa", "priority": "P2", "status": "open",
        "source": "KNOWN_ISSUES K-21", "estimated_minutes": 240,
    },
    {
        "title": "Referral tree gen 1-10 recursion fake — only gen 1 counted",
        "description": "main.py referral tree endpoint counts Gen 1 only despite UI claiming Gen 1-10 total. Recursive CTE query needed.",
        "category": "code", "priority": "P2", "status": "open",
        "source": "KNOWN_ISSUES K-22", "estimated_minutes": 60,
    },
    {
        "title": "SLH_PRICE_USD hardcoded in creator_economy.py",
        "description": "Contains SLH_PRICE_USD = 121.6 constant. Read from /api/prices single source.",
        "category": "code", "priority": "P2", "status": "open",
        "source": "KNOWN_ISSUES K-23", "estimated_minutes": 15,
    },
    {
        "title": "Consolidate 8 versions of airdrop/bot.py",
        "description": "bot.py, bot_v2.py, bot_fixed.py, etc. Consolidate to one, delete rest.",
        "category": "code", "priority": "P2", "status": "open",
        "source": "KNOWN_ISSUES K-24", "estimated_minutes": 30,
    },
    {
        "title": "Duplicate BOT_ID 8530795944 in .env",
        "description": "EXPERTNET_BOT_TOKEN + SLH_AIR_TOKEN share same ID — one stale. Rotate via BotFather.",
        "category": "infra", "priority": "P2", "status": "open",
        "assignee_name": "Osif", "source": "KNOWN_ISSUES K-25", "estimated_minutes": 5,
    },

    # ─── CRM / Community / QA ────────────────────────────────
    {
        "title": "Import Eliezer's 130-investor CSV",
        "description": "Eliezer (@P22PPPPPP, 8088324234) has 130 contacts. Endpoint /api/ambassador/import ready. Needs CSV in UTF-8 format.",
        "category": "crm", "priority": "P1", "status": "blocked",
        "blocker": "Waiting for Eliezer to deliver CSV",
        "assignee_name": "Eliezer", "assignee_telegram_id": 8088324234,
        "source": "DROP_CRM_BUSINESS step 1", "estimated_minutes": 60,
    },
    {
        "title": "Yahav onboarding DM bounce — needs /start @SLH_AIR_bot",
        "description": "Telegram ID 7940057720 bounced broadcast because hasn't initiated bot. Contact him, have him /start, then resend DM.",
        "category": "community", "priority": "P1", "status": "open",
        "assignee_name": "Elazar", "source": "DROP_COMMUNITY #1", "estimated_minutes": 10,
    },
    {
        "title": "Weekly community broadcast (Sun 10:00)",
        "description": "Template in DROP_COMMUNITY_TELEGRAM.md §3.1. Recurring weekly. Mark done weekly, recreate for next week.",
        "category": "community", "priority": "P2", "status": "open",
        "assignee_name": "Elazar", "source": "DROP_COMMUNITY #3.1", "estimated_minutes": 15,
    },
    {
        "title": "QA Session #1 — Golden Paths 1-5",
        "description": "Registration, Academia, Navigation 43 pages, Mobile UX, Mini App. See DROP_QA_TESTING.md.",
        "category": "qa", "priority": "P2", "status": "blocked",
        "blocker": "Waiting for Railway deploy + website push",
        "assignee_name": "Zohar", "source": "DROP_QA_TESTING", "estimated_minutes": 90,
    },

    # ─── Strategic (Owner decisions) ─────────────────────────
    {
        "title": "Strategic decision: Legal entity for real trading",
        "description": "Biggest single blocker to real monetization. Options: חברה בע'מ, עוסק מורשה, פטור. Requires legal consultation.",
        "category": "strategic", "priority": "P1", "status": "open",
        "assignee_name": "Osif", "assignee_telegram_id": 224223270,
        "source": "Roadmap 13+ H", "estimated_minutes": 480,
    },
    {
        "title": "Strategic decision: Phase 2 Identity Proxy architecture",
        "description": "Unified Gateway for all 25 bots vs per-bot auth. See TELEGRAM_FIRST_MIGRATION_PLAN.md.",
        "category": "strategic", "priority": "P2", "status": "open",
        "assignee_name": "Osif", "source": "OPEN_TASKS #19", "estimated_minutes": 120,
    },
    {
        "title": "Strategic decision: Mobile App MVP (RN / Flutter / PWA)",
        "description": "2-3 week development cycle. Decide framework first.",
        "category": "strategic", "priority": "P2", "status": "open",
        "assignee_name": "Osif", "source": "OPEN_TASKS #23", "estimated_minutes": 60,
    },
]


def main():
    admin_key = os.getenv("ADMIN_API_KEY") or os.getenv("ADMIN_BROADCAST_KEY")
    if not admin_key:
        print("ERROR: set ADMIN_API_KEY env var")
        sys.exit(1)

    payload = {"tasks": TASKS, "skip_duplicates_by_source": True}
    req = urllib.request.Request(
        f"{API_BASE}/api/admin/tasks/bulk-import",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Admin-Key": admin_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR {e.code}: {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: connection failed — {e.reason}")
        sys.exit(1)

    print(f"✓ imported {result['inserted']} tasks")
    print(f"  skipped {result['skipped']} duplicates")
    if result["errors"]:
        print(f"  ERRORS: {result['errors']}")


if __name__ == "__main__":
    main()

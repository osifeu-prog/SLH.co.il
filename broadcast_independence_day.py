#!/usr/bin/env python3
# SLH Spark — Independence Day Broadcast (2026)
# Gift: 78 ZVK + 78 REP per registered user
# Message: Happy 78th Independence Day

import os, sys, asyncio, asyncpg, aiohttp
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL missing.")

AIRDROP_BOT_TOKEN = os.getenv("AIRDROP_BOT_TOKEN")
if not AIRDROP_BOT_TOKEN:
    raise SystemExit("AIRDROP_BOT_TOKEN missing.")

TELEGRAM_API = f"https://api.telegram.org/bot{AIRDROP_BOT_TOKEN}"

GIFT = {"ZVK": 78, "REP": 78}

# Fake/test IDs to skip
SKIP_IDS = {100001, 100002, 100003, 200001}

MESSAGE = (
    "🇮🇱 *יום העצמאות השמח! חג עצמאות שמח!* 🇮🇱\n\n"
    "78 שנה למדינת ישראל — ואנחנו חוגגים יחד!\n\n"
    "🎁 *מתנה אישית מאיתנו:*\n"
    "• ZVK: +78 (כנגד 78 שנות עצמאות)\n"
    "• REP: +78 (מוניטין בונוס חגיגי)\n\n"
    "💛 תודה שאתם חלק מקהילת SLH Spark.\n"
    "ביחד אנחנו בונים את הכלכלה הדיגיטלית הישראלית.\n\n"
    "🔗 [slh-nft.com](https://slh-nft.com) | /wallet לצפייה ביתרה"
)

async def get_real_users(pool):
    rows = await pool.fetch(
        "SELECT telegram_id, first_name, username FROM web_users "
        "WHERE telegram_id IS NOT NULL AND telegram_id > 0"
    )
    return [r for r in rows if r["telegram_id"] not in SKIP_IDS]

async def give_gift(pool, telegram_id, token, amount):
    await pool.execute("""
        INSERT INTO token_balances (user_id, token, balance, updated_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id, token) DO UPDATE
        SET balance = token_balances.balance + EXCLUDED.balance, updated_at = NOW()
    """, telegram_id, token, amount)

async def send_tg(session, chat_id, text):
    try:
        async with session.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as r:
            data = await r.json()
            return data.get("ok", False), data.get("description", "")
    except Exception as e:
        return False, str(e)

async def main():
    pool = await asyncpg.create_pool(DATABASE_URL)
    try:
        users = await get_real_users(pool)
        ts = datetime.now().isoformat()

        print(f"\n{'='*60}")
        print(f"INDEPENDENCE DAY BROADCAST — {ts}")
        print(f"Gift: ZVK+78, REP+78 | Users: {len(users)}")
        print(f"{'='*60}\n")

        # Step 1: credit tokens
        tx = 0
        for u in users:
            for token, amount in GIFT.items():
                await give_gift(pool, u["telegram_id"], token, amount)
                tx += 1
        print(f"[DB] {tx} token transactions written.\n")

        # Step 2: send Telegram messages
        sent = failed = 0
        async with aiohttp.ClientSession() as session:
            for u in users:
                ok, err = await send_tg(session, u["telegram_id"], MESSAGE)
                name = u["first_name"] or u["username"] or str(u["telegram_id"])
                if ok:
                    sent += 1
                    print(f"   ✅ {name} ({u['telegram_id']})")
                else:
                    failed += 1
                    print(f"   ❌ {name} ({u['telegram_id']}) — {err}")
                await asyncio.sleep(0.05)

        # Step 3: log to broadcast_log
        await pool.execute("""
            INSERT INTO broadcast_log
                (sent_at, target, total_targets, success_count, fail_count, message_preview, admin_actor)
            VALUES (NOW(), 'ALL_USERS', $1, $2, $3,
                    'INDEPENDENCE_DAY_78: ZVK+78 REP+78', 'scheduled_task')
        """, len(users), sent, failed)

        print(f"\n{'='*60}")
        print(f"✅ Completed!")
        print(f"   Users targeted : {len(users)}")
        print(f"   TG sent        : {sent}")
        print(f"   TG failed      : {failed}")
        print(f"   Token txns     : {tx}")
        print(f"   Gift per user  : ZVK+78, REP+78")
        print(f"{'='*60}\n")

    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())

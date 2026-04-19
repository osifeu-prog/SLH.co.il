#!/usr/bin/env python3
# ============================================================
# SLH SPARK — Broadcast Airdrop Script
# Runs at 19:45 daily
# Distributes tokens to all users + sends Telegram notification
# ============================================================

import os
import sys
import asyncpg
import asyncio
import aiohttp
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Connect via DATABASE_URL env var. Railway proxy URL lives in .env / Railway Variables — never hardcode.
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL missing. Set it in .env or Railway Variables.")

AIRDROP_BOT_TOKEN = os.getenv("AIRDROP_BOT_TOKEN")
if not AIRDROP_BOT_TOKEN:
    raise SystemExit("AIRDROP_BOT_TOKEN missing. Set it in .env.")

TELEGRAM_API = f"https://api.telegram.org/bot{AIRDROP_BOT_TOKEN}"

# Airdrop amounts per user (per Osif's spec)
AIRDROP = {
    "SLH": 0.12,
    "ZVK": 8,
    "MNH": 32,
    "REP": 12,
    "ZUZ": 100
}

AIRDROP_MESSAGE = (
    "🎁 *קיבלת Airdrop יומי מ-SLH Spark!*\n\n"
    "💰 הנכסים שנוספו לארנקך:\n"
    "• SLH: +0.12\n"
    "• ZVK: +8\n"
    "• MNH: +32\n"
    "• REP: +12\n"
    "• ZUZ: +100\n\n"
    "📊 לצפייה ביתרה המעודכנת: /wallet\n"
    "🔗 [slh-nft.com](https://slh-nft.com)"
)

async def get_all_users(pool):
    """Get all registered users from web_users"""
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id FROM web_users WHERE telegram_id IS NOT NULL")
        return [u['telegram_id'] for u in users]

async def give_airdrop(pool, user_id, token, amount):
    """Give token to user (insert or update)"""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO token_balances (user_id, token, balance, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id, token) DO UPDATE
            SET balance = token_balances.balance + EXCLUDED.balance, updated_at = NOW()
        """, user_id, token, amount)

async def send_telegram_message(session, chat_id, text):
    """Send Telegram message to a user, return True/False"""
    try:
        async with session.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            data = await resp.json()
            if data.get("ok"):
                return True
            else:
                print(f"   ⚠️  TG error for {chat_id}: {data.get('description', 'unknown')}")
                return False
    except Exception as e:
        print(f"   ❌ TG exception for {chat_id}: {e}")
        return False

async def broadcast_airdrop():
    """Main broadcast function"""
    pool = await asyncpg.create_pool(DATABASE_URL)

    try:
        users = await get_all_users(pool)
        timestamp = datetime.now().isoformat()

        print(f"\n{'='*60}")
        print(f"BROADCAST AIRDROP - {timestamp}")
        print(f"{'='*60}")
        print(f"Distributing to {len(users)} users...\n")

        # Step 1: Update token balances
        tx_count = 0
        for user_id in users:
            for token, amount in AIRDROP.items():
                await give_airdrop(pool, user_id, token, amount)
                tx_count += 1

        print(f"[DB] {tx_count} token transactions written.\n")

        # Step 2: Send Telegram notifications
        sent = 0
        failed = 0
        async with aiohttp.ClientSession() as session:
            for user_id in users:
                ok = await send_telegram_message(session, user_id, AIRDROP_MESSAGE)
                if ok:
                    sent += 1
                    print(f"   ✅ Sent to {user_id}")
                else:
                    failed += 1
                await asyncio.sleep(0.05)  # Avoid Telegram rate limit

        print(f"\n[OK] Completed!")
        print(f"   - Users: {len(users)}")
        print(f"   - Token transactions: {tx_count}")
        print(f"   - TG messages sent: {sent}")
        print(f"   - TG messages failed: {failed}")
        print(f"\nDistribution per user:")
        for token, amount in AIRDROP.items():
            print(f"   - {token}: +{amount}")

        # Log summary to broadcast_log
        await pool.execute("""
            INSERT INTO broadcast_log (sent_at, target, total_targets, success_count, fail_count, message_preview, admin_actor)
            VALUES (NOW(), 'ALL_USERS', $1, $2, $3, 'AIRDROP: SLH+ZVK+MNH+REP+ZUZ', 'scheduled_task')
        """, len(users), sent, failed)

    finally:
        await pool.close()
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(broadcast_airdrop())

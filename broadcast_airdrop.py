#!/usr/bin/env python3
# ============================================================
# SLH SPARK — Broadcast Airdrop Script
# Runs at 19:45 daily
# Distributes tokens to all users
# ============================================================

import os
import asyncpg
import asyncio
from datetime import datetime
import json

# Connect via DATABASE_URL env var. Railway proxy URL lives in .env / Railway Variables — never hardcode.
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL missing. Set it in .env or Railway Variables.")

# Airdrop amounts per user (per Osif's spec)
AIRDROP = {
    "SLH": 0.12,
    "ZVK": 8,
    "MNH": 32,
    "REP": 12,
    "ZUZ": 100  # Fraud reporting tokens
}

async def get_all_users(pool):
    """Get all registered users from web_users"""
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id FROM web_users")
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

        count = 0
        for user_id in users:
            for token, amount in AIRDROP.items():
                await give_airdrop(pool, user_id, token, amount)
                count += 1

        print(f"\n[OK] Completed!")
        print(f"   - Users: {len(users)}")
        print(f"   - Tokens: {list(AIRDROP.keys())}")
        print(f"   - Transactions: {count}")
        print(f"\nDistribution per user:")
        for token, amount in AIRDROP.items():
            print(f"   - {token}: {amount}")

        # Log summary to broadcast_log
        await pool.execute("""
            INSERT INTO broadcast_log (sent_at, target, total_targets, success_count, fail_count, message_preview, admin_actor)
            VALUES (NOW(), 'ALL_USERS', $1, $1, 0, 'AIRDROP: SLH+ZVK+MNH+REP+ZUZ', 'scheduled_task')
        """, len(users))

    finally:
        await pool.close()
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(broadcast_airdrop())

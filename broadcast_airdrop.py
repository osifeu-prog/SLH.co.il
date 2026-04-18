#!/usr/bin/env python3
# ============================================================
# SLH SPARK — Broadcast Airdrop Script
# Runs at 19:45 daily
# Distributes tokens to all users
# ============================================================

import asyncpg
import asyncio
from datetime import datetime
import json

DATABASE_URL = "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"

# Airdrop amounts per user (per Osif's spec)
AIRDROP = {
    "SLH": 0.12,
    "ZVK": 8,
    "MNH": 32,
    "REP": 12,
    "ZUZ": 100  # Fraud reporting tokens
}

async def get_all_users(pool):
    """Get all registered users"""
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id FROM users")
        return [u['user_id'] for u in users]

async def give_airdrop(pool, user_id, token, amount):
    """Give token to user (insert or update)"""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO token_balances (user_id, token, balance, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id, token) DO UPDATE
            SET balance = balance + $3, updated_at = NOW()
        """, user_id, token, amount)

        # Log in audit log
        await conn.execute("""
            INSERT INTO audit_log (user_id, event_type, payload_json)
            VALUES ($1, 'AIRDROP', $2)
        """, user_id, json.dumps({
            "token": token,
            "amount": amount,
            "broadcast": "19:45_daily"
        }))

async def broadcast_airdrop():
    """Main broadcast function"""
    pool = await asyncpg.create_pool(DATABASE_URL)

    try:
        users = await get_all_users(pool)
        timestamp = datetime.now().isoformat()

        print(f"\n{'='*60}")
        print(f"🚀 BROADCAST AIRDROP — {timestamp}")
        print(f"{'='*60}")
        print(f"Distributing to {len(users)} users...\n")

        count = 0
        for user_id in users:
            for token, amount in AIRDROP.items():
                await give_airdrop(pool, user_id, token, amount)
                count += 1

        print(f"\n✅ Completed!")
        print(f"   • Users: {len(users)}")
        print(f"   • Tokens: {list(AIRDROP.keys())}")
        print(f"   • Transactions: {count}")
        print(f"\n📋 Distribution per user:")
        for token, amount in AIRDROP.items():
            print(f"   • {token}: {amount}")

        # Log summary
        await pool.execute("""
            INSERT INTO audit_log (event_type, payload_json)
            VALUES ('BROADCAST_SUMMARY', $1)
        """, json.dumps({
            "users_count": len(users),
            "tokens": AIRDROP,
            "timestamp": timestamp
        }))

    finally:
        await pool.close()
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(broadcast_airdrop())

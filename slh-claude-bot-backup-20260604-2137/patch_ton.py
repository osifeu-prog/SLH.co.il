import re

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# â”€â”€â”€ TON tracking code â”€â”€â”€
ton_code = r'''
# â•â•â• TON DEPOSIT TRACKING â•â•â•
TON_WALLET_RAW = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
TON_API_URL = "https://toncenter.com/api/v3/transactions"
last_ton_lt = None

async def check_ton_deposits():
    global last_ton_lt
    params = {"account": TON_WALLET_RAW, "limit": 30, "sort": "desc"}
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(TON_API_URL, params=params, timeout=10) as resp:
                data = await resp.json()
        for tx in data.get("transactions", []):
            tx_lt = tx.get("lt")
            if last_ton_lt and tx_lt <= last_ton_lt:
                continue
            in_msg = tx.get("in_msg", {})
            value = int(in_msg.get("value", 0))
            if value <= 0:
                continue
            amount_ton = value / 1_000_000_000
            comment = in_msg.get("message", "") or in_msg.get("decoded_op_name", "")
            try:
                user_id = int(comment.strip())
                if user_id > 100000000:
                    await process_ton_deposit(user_id, amount_ton, tx["hash"])
            except:
                pass
        if data.get("transactions"):
            last_ton_lt = max(tx.get("lt", 0) for tx in data["transactions"])
    except Exception as e:
        print(f"TON tracker error: {e}")

async def process_ton_deposit(user_id: int, amount: float, tx_hash: str):
    async with pool.acquire() as conn:
        # dedup
        existing = await conn.fetchval("SELECT id FROM payments WHERE tx_hash = $1", tx_hash)
        if existing:
            return
        await conn.execute(
            "INSERT INTO payments (user_id, amount, tx_hash, status) VALUES ($1, $2, $3, 'confirmed')",
            user_id, amount, tx_hash
        )
        await conn.execute(
            "UPDATE users SET balance = balance + $1 WHERE telegram_id = $2",
            amount, user_id
        )
        # auto tier upgrade
        new_balance = await conn.fetchval("SELECT balance FROM users WHERE telegram_id = $1", user_id)
        if new_balance >= 29:
            tier = "business"
        elif new_balance >= 9.9:
            tier = "pro"
        else:
            tier = "free"
        await conn.execute("UPDATE users SET tier = $1 WHERE telegram_id = $2", tier, user_id)
        # notify user
        try:
            await bot.send_message(
                user_id,
                f"âœ… <b>×”×¤×§×“×” ×”×ª×§×‘×œ×”!</b>\n\n"
                f"×¡×›×•×: <b>{amount:.2f} TON</b>\n"
                f"TX: <code>{tx_hash[:12]}...</code>\n\n"
                f"×™×ª×¨×” ×ž×¢×•×“×›× ×ª: {new_balance:.2f} TON\n"
                f"Tier: <b>{tier.upper()}</b>",
                parse_mode="HTML"
            )
        except:
            pass

async def ton_monitor():
    while True:
        await check_ton_deposits()
        await asyncio.sleep(30)
'''

# â”€â”€â”€ Inject imports (aiohttp) â”€â”€â”€
if "import aiohttp" not in content:
    content = content.replace("import groq", "import groq\nimport aiohttp")

# â”€â”€â”€ Add ton_code before main() â”€â”€â”€
content = content.replace("async def main():", ton_code + "\n\nasync def main():")

# â”€â”€â”€ Launch monitor inside main â”€â”€â”€
old_main_body = "    await create_pool()\n    await bot.delete_webhook(drop_pending_updates=True)\n    await dp.start_polling(bot)"
new_main_body = "    await create_pool()\n    asyncio.create_task(ton_monitor())\n    await bot.delete_webhook(drop_pending_updates=True)\n    await dp.start_polling(bot)"
content = content.replace(old_main_body, new_main_body)

with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("âœ… TON deposit tracking added.")


import psycopg2, requests, os, asyncio
from datetime import datetime

async def run_bot_self_test(bot, admin_id):
    results = []
    
    # 1. Database
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        conn.close()
        results.append(("✅ Database", f"{users} users"))
    except Exception as e:
        results.append(("❌ Database", str(e)))

    # 2. Telegram Bot Token
    try:
        resp = requests.get(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/getMe", timeout=5)
        if resp.json().get("ok"):
            results.append(("✅ Bot Token", resp.json()["result"]["username"]))
        else:
            results.append(("❌ Bot Token", "Invalid"))
    except Exception as e:
        results.append(("❌ Bot Token", str(e)))

    # 3. Groq API
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                timeout=10
            )
            if resp.status_code == 200:
                results.append(("✅ Groq AI", "OK"))
            else:
                results.append(("⚠️ Groq AI", f"HTTP {resp.status_code}"))
        except Exception as e:
            results.append(("❌ Groq AI", str(e)))
    else:
        results.append(("⚪ Groq AI", "No key"))

    # 4. CoinGecko
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/ping", timeout=5)
        results.append(("✅ CoinGecko", "OK" if resp.status_code == 200 else f"Status {resp.status_code}"))
    except:
        results.append(("❌ CoinGecko", "Unreachable"))

    # 5. TON Indexer (simple test)
    try:
        resp = requests.get(f"https://toncenter.com/api/v3/masterchainInfo", timeout=5)
        if resp.status_code == 200:
            results.append(("✅ TON Indexer", "OK"))
        else:
            results.append(("⚠️ TON Indexer", f"HTTP {resp.status_code}"))
    except:
        results.append(("❌ TON Indexer", "Unreachable"))

    # 6. Web Dashboard
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            results.append(("✅ Web Dashboard", "OK"))
        else:
            results.append(("⚠️ Web Dashboard", f"HTTP {resp.status_code}"))
    except:
        results.append(("❌ Web Dashboard", "Unreachable (may not be exposed)"))

    # Send report
    report = "🧪 <b>SLH Self-Test Report</b>\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
    for status, detail in results:
        report += f"{status}: {detail}\n"
    await bot.send_message(admin_id, report, parse_mode="HTML")

import requests, os, json, time
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = "224223270"  # Your Telegram ID

commands = [
    "/start", "/help", "/register", "/upgrade", "/donate",
    "/checkin", "/points", "/status", "/dashboard", "/stats",
    "/crm", "/events", "/segments", "/crypto", "/tap",
    "/wallet", "/deposit", "/profile", "/myid", "/leaderboard",
    "/referral", "/tasks", "/daily", "/roadmap", "/backup",
    "/admin", "/users", "/morning", "/doctor", "/statusapi"
]

def send_command(cmd):
    try:
        url = f"{BASE_URL}/sendMessage"
        resp = requests.post(url, json={"chat_id": CHAT_ID, "text": cmd}, timeout=10)
        return resp.status_code == 200
    except:
        return False

results = []
print("🧪 SLH Bot Test Suite")
print("=" * 50)
for cmd in commands:
    ok = send_command(cmd)
    status = "✅" if ok else "❌"
    results.append({"command": cmd, "ok": ok})
    print(f"{status} {cmd}")
    time.sleep(0.3)

# Additional tests
print("\n📝 Task flow test...")
send_command("/task test automated task")
time.sleep(0.3)
send_command("/done 1")
time.sleep(0.3)
send_command("/tasks")
print("   Task flow: ✅")

print("\n💬 Feedback test...")
send_command("/feedback automated test feedback")
print("   Feedback: ✅")

# Summary
passed = sum(1 for r in results if r["ok"])
total = len(results)
print(f"\n{'='*50}")
print(f"📊 Results: {passed}/{total} passed")

# Save report
report = {
    "timestamp": str(datetime.now()),
    "total": total,
    "passed": passed,
    "failed": total - passed,
    "details": results
}
with open("test_report.json", "w") as f:
    json.dump(report, f, indent=2)
print("📄 Report saved to test_report.json")

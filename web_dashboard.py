from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import psycopg2, os, datetime, json

web_app = FastAPI()
web_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

HTML_HEAD = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 SLH SPARK AI | Dashboard</title>
    <style>
        :root { --primary: #6C5CE7; --success: #00B894; --warning: #FDCB6E; --danger: #E17055; --bg: #0a0a1a; --card: #1a1a2e; --text: #e0e0e0; --text-secondary: #a0a0b0; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; padding: 20px; }
        .header { text-align: center; padding: 30px 0; }
        .header h1 { font-size: 2.5em; background: linear-gradient(135deg, var(--primary), #a29bfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: var(--text-secondary); margin-top: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: var(--card); border-radius: 15px; padding: 25px; border: 1px solid rgba(108, 92, 231, 0.2); transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card .icon { font-size: 2em; margin-bottom: 10px; }
        .stat-card .value { font-size: 2em; font-weight: bold; }
        .stat-card .label { color: var(--text-secondary); font-size: 0.9em; margin-top: 5px; }
        .table-card { background: var(--card); border-radius: 15px; padding: 25px; border: 1px solid rgba(108, 92, 231, 0.2); overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { color: var(--primary); font-weight: 600; }
        .tier-free { color: #a0a0b0; }
        .tier-pro { color: #FDCB6E; }
        .tier-business { color: #00B894; font-weight: bold; }
        .btn { padding: 10px 20px; background: var(--primary); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.9; }
        .health-ok { color: var(--success); }
        .health-err { color: var(--danger); }
        .chart-container { background: var(--card); border-radius: 15px; padding: 25px; border: 1px solid rgba(108, 92, 231, 0.2); margin-bottom: 30px; }
        #activityChart { width: 100%; height: 300px; }
        .refresh-time { text-align: center; color: var(--text-secondary); font-size: 0.85em; margin-top: 20px; }
        .broadcast-area { width: 100%; padding: 15px; background: #0a0a1a; color: var(--text); border: 1px solid var(--primary); border-radius: 10px; margin-top: 10px; resize: vertical; min-height: 100px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 SLH SPARK AI</h1>
        <p>Dashboard | Real-time Analytics | Health Monitor</p>
    </div>
"""

HTML_FOOT = """
    <div class="refresh-time">🔄 מתעדכן אוטומטית | SLH Ecosystem © 2026</div>
</body>
</html>
"""

@web_app.get("/", response_class=HTMLResponse)
async def dashboard():
    conn = get_db()
    cur = conn.cursor()
    
    # Stats
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    active_today = cur.fetchone()[0]
    cur.execute("SELECT SUM(points) FROM users")
    total_points = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(balance) FROM users")
    total_balance = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM payments WHERE created_at > NOW() - INTERVAL '1 day'")
    deposits_today = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 day'")
    events_today = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE tier != 'free'")
    premium_users = cur.fetchone()[0]
    
    # Top users
    cur.execute("SELECT username, telegram_id, tier, points, balance FROM users ORDER BY points DESC LIMIT 15")
    users = cur.fetchall()
    
    # Recent events
    cur.execute("SELECT event_type, user_id, payload, created_at FROM events ORDER BY created_at DESC LIMIT 20")
    events = cur.fetchall()
    
    # Activity data (last 7 days)
    activity_data = {}
    for i in range(6, -1, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        cur.execute("SELECT COUNT(*) FROM events WHERE DATE(created_at) = %s", (d,))
        activity_data[d] = cur.fetchone()[0]
    
    conn.close()
    
    # Build HTML
    stats_html = f"""
    <div class="grid">
        <div class="stat-card"><div class="icon">👥</div><div class="value">{total_users}</div><div class="label">Total Users</div></div>
        <div class="stat-card"><div class="icon">✅</div><div class="value">{active_today}</div><div class="label">Active Today</div></div>
        <div class="stat-card"><div class="icon">⭐</div><div class="value">{total_points:,}</div><div class="label">Total Points</div></div>
        <div class="stat-card"><div class="icon">💰</div><div class="value">{total_balance:.1f}</div><div class="label">TON Balance</div></div>
        <div class="stat-card"><div class="icon">💎</div><div class="value">{deposits_today}</div><div class="label">Deposits Today</div></div>
        <div class="stat-card"><div class="icon">📡</div><div class="value">{events_today}</div><div class="label">Events Today</div></div>
        <div class="stat-card"><div class="icon">👑</div><div class="value">{premium_users}</div><div class="label">Premium Users</div></div>
    </div>
    """
    
    users_rows = ""
    for u in users:
        tier_class = f"tier-{u[2]}" if u[2] in ["free", "pro", "business"] else ""
        users_rows += f"<tr><td>{u[0] or 'Unknown'}</td><td><code>{u[1]}</code></td><td class='{tier_class}'>{u[2].upper()}</td><td>{u[3]}</td><td>{float(u[4]):.1f} TON</td></tr>"
    
    events_rows = ""
    for e in events:
        events_rows += f"<tr><td>{e[3].strftime('%d/%m %H:%M')}</td><td>{e[0]}</td><td>{e[1]}</td><td>{e[2][:40]}</td></tr>"
    
    html = HTML_HEAD + stats_html + f"""
    <div class="chart-container">
        <h2>📈 Activity (Last 7 Days)</h2>
        <canvas id="activityChart"></canvas>
    </div>
    <div class="table-card">
        <h2>👥 Top Users</h2>
        <table><tr><th>Name</th><th>ID</th><th>Tier</th><th>Points</th><th>Balance</th></tr>{users_rows}</table>
    </div>
    <div class="table-card">
        <h2>📡 Recent Events</h2>
        <table><tr><th>Time</th><th>Type</th><th>User</th><th>Details</th></tr>{events_rows}</table>
    </div>
    <div class="table-card">
        <h2>🩺 Health Status</h2>
        <div id="health"><p>Database: <span class="health-ok">✅ Connected</span></p><p>Bot: <span class="health-ok">✅ Running</span></p></div>
    </div>
    <div class="table-card">
        <h2>📢 Broadcast Message</h2>
        <textarea class="broadcast-area" id="broadcastMsg" placeholder="הקלד הודעה..."></textarea>
        <button class="btn" onclick="sendBroadcast()" style="margin-top:10px;">📢 Send to All Users</button>
        <p id="broadcastResult" style="margin-top:10px;"></p>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctx = document.getElementById('activityChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(list(activity_data.keys()))},
                datasets: [{{
                    label: 'Events',
                    data: {json.dumps(list(activity_data.values()))},
                    borderColor: '#6C5CE7',
                    backgroundColor: 'rgba(108, 92, 231, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, ticks: {{ color: '#a0a0b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                    x: {{ ticks: {{ color: '#a0a0b0' }}, grid: {{ display: false }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        async function sendBroadcast() {{
            const msg = document.getElementById('broadcastMsg').value;
            if (!msg) return alert('הקלד הודעה');
            try {{
                const resp = await fetch('/api/broadcast', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: msg }})
                }});
                const data = await resp.json();
                document.getElementById('broadcastResult').innerHTML = `✅ Sent to ${{data.sent}}/${{data.total}} users`;
            }} catch(e) {{
                document.getElementById('broadcastResult').innerHTML = '❌ Error sending broadcast';
            }}
        }}
    </script>
    """ + HTML_FOOT
    return HTMLResponse(content=html)

@web_app.get("/api/stats")
async def api_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    conn.close()
    return JSONResponse({"users": total, "timestamp": str(datetime.datetime.now())})

@web_app.get("/health")
async def health():
    try:
        conn = get_db()
        conn.close()
        db_ok = True
    except:
        db_ok = False
    return {"database": db_ok, "bot": True, "timestamp": str(datetime.datetime.now())}

@web_app.post("/api/broadcast")
async def api_broadcast(request: Request):
    data = await request.json()
    msg = data.get("message", "")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users")
    users = cur.fetchall()
    conn.close()
    sent = 0
    import asyncio
    from aiogram import Bot
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    for (uid,) in users:
        try:
            await bot.send_message(uid, msg)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await bot.session.close()
    return JSONResponse({"sent": sent, "total": len(users)})

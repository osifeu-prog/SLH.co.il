import sqlite3
import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)
DB_PATH = 'vault/expertnet.db'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ExpertNet Admin Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { background-color: #0f172a; color: white; font-family: sans-serif; padding: 40px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #fbbf24; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
        th { color: #fbbf24; }
        .stat-box { display: inline-block; padding: 20px; background: #334155; border-radius: 8px; margin-right: 20px; }
        .highlight { color: #fbbf24; font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>ExpertNet Core <span style="color:#fbbf24">v3.0</span></h1>
    <div style="margin-bottom: 30px;">
        <div class="stat-box">Total Users: <br><span class="highlight">{{ total_users }}</span></div>
        <div class="stat-box">Total Community Value: <br><span class="highlight">{{ total_balance }} BNB</span></div>
    </div>
    <div class="card">
        <h3>Verified Members List</h3>
        {{ table_html | safe }}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if not os.path.exists(DB_PATH):
        return "Waiting for first user to register..."
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT date, name, balance, tg_id FROM users ORDER BY id DESC", conn)
    conn.close()
    
    total_users = len(df)
    total_balance = round(df['balance'].sum(), 4)
    table_html = df.to_html(classes='table', index=False)
    
    return render_template_string(HTML_TEMPLATE, 
                                total_users=total_users, 
                                total_balance=total_balance, 
                                table_html=table_html)

if __name__ == '__main__':
    app.run(port=5000)
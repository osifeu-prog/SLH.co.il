import json, matplotlib.pyplot as plt
import psutil
from datetime import datetime

# טען את הדו״ח JSON אם קיים
try:
    data = json.load(open("test_report.json"))
except:
    data = {"status":"no report","checks":[]}

html = "<html><head><title>SLH Diagnostic Report</title></head><body>"
html += f"<h1>SLH Diagnostic Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}</h1>"
html += f"<p><b>Status:</b> {data.get('status','unknown')}</p>"

html += "<table border=1 cellpadding=5><tr><th>Check</th><th>Result</th><th>Severity</th></tr>"
for check in data.get("checks", []):
    html += f"<tr><td>{check.get('name')}</td><td>{check.get('result')}</td><td>{check.get('severity')}</td></tr>"
html += "</table>"

# גרף Latency
latencies = [c.get("latency") for c in data.get("checks", []) if "latency" in c]
if latencies:
    plt.figure(figsize=(6,4))
    plt.plot(latencies, marker="o")
    plt.title("Response Times")
    plt.xlabel("Check #")
    plt.ylabel("ms")
    plt.savefig("latency.png")
    html += "<h2>Response Times</h2><img src='latency.png'>"

# גרף CPU
cpu = psutil.cpu_percent(interval=1, percpu=True)
plt.figure(figsize=(6,4))
plt.bar(range(len(cpu)), cpu)
plt.title("CPU Usage per Core")
plt.xlabel("Core")
plt.ylabel("%")
plt.savefig("cpu.png")
html += "<h2>CPU Usage</h2><img src='cpu.png'>"

# גרף Memory
mem = psutil.virtual_memory()
plt.figure(figsize=(6,4))
plt.bar(["Used","Free"], [mem.used/1024**3, mem.available/1024**3])
plt.title("Memory Usage (GB)")
plt.savefig("memory.png")
html += "<h2>Memory Usage</h2><img src='memory.png'>"

html += "</body></html>"
open("test_report.html","w",encoding="utf-8").write(html)
print("📊 HTML report generated: test_report.html with advanced graphs")

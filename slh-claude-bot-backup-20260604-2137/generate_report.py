
import json, matplotlib.pyplot as plt
from datetime import datetime

# ×˜×¢×Ÿ ××ª ×”×“×•×´×— JSON ×× ×§×™×™×
try:
    data = json.load(open("test_report.json"))
except:
    data = {"status":"no report","checks":[]}

html = "<html><head><title>SLH Diagnostic Report</title></head><body>"
html += f"<h1>SLH Diagnostic Report â€” {datetime.now().strftime('%Y-%m-%d %H:%M')}</h1>"
html += f"<p><b>Status:</b> {data.get('status','unknown')}</p>"

html += "<table border=1 cellpadding=5><tr><th>Check</th><th>Result</th><th>Severity</th></tr>"
for check in data.get("checks", []):
    html += f"<tr><td>{check.get('name')}</td><td>{check.get('result')}</td><td>{check.get('severity')}</td></tr>"
html += "</table>"

latencies = [c.get("latency") for c in data.get("checks", []) if "latency" in c]
if latencies:
    plt.figure(figsize=(6,4))
    plt.plot(latencies, marker="o")
    plt.title("Response Times")
    plt.xlabel("Check #")
    plt.ylabel("ms")
    plt.savefig("latency.png")
    html += "<h2>Response Times</h2><img src='latency.png'>"

html += "</body></html>"
open("test_report.html","w",encoding="utf-8").write(html)
print("ðŸ“Š HTML report generated: test_report.html")


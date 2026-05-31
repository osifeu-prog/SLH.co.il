from flask import Flask, send_file, render_template_string
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    controls = """
    <h1 style='color:#2E86C1'>SLH Control Panel</h1>
    <p>
      <a href='/restart'>🔄 Restart Bot</a> |
      <a href='/stop'>⏹ Stop Bot</a> |
      <a href='/tests'>🧪 Run Tests</a>
    </p>
    <iframe src='/report' width='100%' height='600'></iframe>
    """
    return render_template_string(controls)

@app.route("/report")
def report():
    return send_file("test_report.html")

@app.route("/latency")
def latency():
    return send_file("latency.png")

@app.route("/restart")
def restart():
    subprocess.run(["railway","down","--service","slh-AI-bot"])
    subprocess.run(["railway","up","--service","slh-AI-bot"])
    return "<p>🔄 Bot restarted. Wait ~40s.</p><a href='/'>Back</a>"

@app.route("/stop")
def stop():
    subprocess.run(["railway","down","--service","slh-AI-bot"])
    return "<p>⏹ Bot stopped.</p><a href='/'>Back</a>"

@app.route("/tests")
def tests():
    subprocess.run(["python","health_check.py"])
    subprocess.run(["python","load_test_correct.py"])
    subprocess.run(["python","bot_tests.py"])
    subprocess.run(["python","fix_all.py"])
    subprocess.run(["python","generate_report.py"])
    return "<p>🧪 Tests complete. Report updated.</p><a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

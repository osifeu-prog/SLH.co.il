from flask import Flask, render_template_string, send_file
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>SLH Control Panel</h1>
    <p>
        <a href='/report'>Report</a> |
        <a href='/tests'>Run Tests</a>
    </p>
    """

@app.route("/report")
def report():
    return send_file("test_report.html")

@app.route("/tests")
def tests():
    subprocess.run(["python", "health_check.py"])
    subprocess.run(["python", "load_test_correct.py"])
    subprocess.run(["python", "bot_tests.py"])
    subprocess.run(["python", "generate_report.py"])
    return "<p>Tests complete</p><a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
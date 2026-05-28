ן»¿"""
Bridge between Telegram bot and Autonomous Agents
Commands: /scan, /plan, /auto
"""
import os, subprocess, json

AGENTS_DIR = r"D:\SLH_Autonomous"

def run_scan(target: str) -> str:
    try:
        result = subprocess.run(
            ["python", os.path.join(AGENTS_DIR, "scan_agent.py"), target],
            capture_output=True, text=True, timeout=60, cwd=AGENTS_DIR
        )
        if result.returncode == 0:
            with open(os.path.join(AGENTS_DIR, "scan_report.json"), "r", encoding="utf-8") as f:
                report = json.load(f)
            return f"Scan done. {report['total_files']} files, {len(report['issues'])} issues."
        return f"Scan error: {result.stderr[:300]}"
    except Exception as e:
        return f"Scan failed: {e}"

def run_plan(goal: str) -> str:
    try:
        result = subprocess.run(
            ["python", os.path.join(AGENTS_DIR, "planning_agent.py")],
            input=goal + "\n", capture_output=True, text=True, timeout=60, cwd=AGENTS_DIR
        )
        if os.path.exists(os.path.join(AGENTS_DIR, "plan.json")):
            with open(os.path.join(AGENTS_DIR, "plan.json"), "r", encoding="utf-8") as f:
                plan = json.load(f)
            lines = [f"[{t['id']}] {t['title']}" for t in plan.get("tasks", [])]
            return "Plan:\n" + "\n".join(lines)
        return result.stdout[:500] or result.stderr[:300]
    except Exception as e:
        return f"Plan failed: {e}"

def run_auto(goal: str) -> str:
    scan_result = run_scan(r"D:\slh-website")
    plan_result = run_plan(goal)
    return f"== SCAN ==\n{scan_result}\n\n== PLAN ==\n{plan_result}"

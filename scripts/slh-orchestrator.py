#!/usr/bin/env python3
"""
SLH Orchestrator — The Local Control Layer
============================================

This script runs LOCALLY (on Osif's machine, or on the VPS that runs the bots).
It is the bridge between:
  - The remote API's control intents (queued in `bot_control_intents` table)
  - The local Docker daemon that actually starts/stops bot containers

Loop (every ORCHESTRATOR_POLL_SECONDS, default 15s):
  1. POST heartbeat to API for the orchestrator itself ("orchestrator-bot")
  2. GET /api/system/intents/pending (auth: X-Orchestrator-Key)
  3. For each pending intent:
       - Execute the corresponding `docker compose ...` command locally
       - POST /api/system/intents/result with success/failure + output
  4. Sleep, repeat

It also runs heartbeats on behalf of all bots whose containers are healthy
(useful when bots themselves don't yet implement the heartbeat call).

Configuration (env vars):
  SLH_API_BASE              default: https://slhcoil-production.up.railway.app
  ORCHESTRATOR_KEY          REQUIRED — must match the API's env var
  ORCHESTRATOR_POLL_SECONDS default: 15
  DOCKER_COMPOSE_FILE       default: D:/SLH_ECOSYSTEM/docker-compose.yml
  DOCKER_COMPOSE_CMD        default: "docker compose" (use "docker-compose" on older systems)
  ORCHESTRATOR_LOG_FILE     default: D:/SLH_ECOSYSTEM/ops/orchestrator.log

Usage:
  python scripts/slh-orchestrator.py                         # run forever
  python scripts/slh-orchestrator.py --once                  # one cycle then exit
  python scripts/slh-orchestrator.py --heartbeats-only       # only push heartbeats
  python scripts/slh-orchestrator.py --check                 # sanity check + exit

Author: Claude (Cowork mode session, 2026-04-27)
"""
import os
import sys
import json
import time
import argparse
import datetime as dt
import subprocess
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any

# ─────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────
API_BASE = os.environ.get("SLH_API_BASE", "https://slhcoil-production.up.railway.app").rstrip("/")
ORCHESTRATOR_KEY = os.environ.get("ORCHESTRATOR_KEY", "")
POLL_SECONDS = int(os.environ.get("ORCHESTRATOR_POLL_SECONDS", "15"))
COMPOSE_FILE = os.environ.get("DOCKER_COMPOSE_FILE", "D:/SLH_ECOSYSTEM/docker-compose.yml")
COMPOSE_CMD = os.environ.get("DOCKER_COMPOSE_CMD", "docker compose")
LOG_FILE = os.environ.get("ORCHESTRATOR_LOG_FILE", "D:/SLH_ECOSYSTEM/ops/orchestrator.log")

EXPECTED_BOTS = [
    "core-bot", "guardian-bot", "botshop", "wallet-bot", "factory-bot",
    "fun-bot", "admin-bot", "airdrop-bot", "campaign-bot", "game-bot",
    "ton-mnh-bot", "slh-ton-bot", "ledger-bot", "osif-shop-bot", "nifti-bot",
    "chance-bot", "nfty-bot", "ts-set-bot", "crazy-panel-bot", "nft-shop-bot",
    "beynonibank-bot", "test-bot", "claude-bot", "academia-bot", "expertnet-bot",
]

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
def log(level: str, msg: str):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {level:5s} {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[orchestrator] Log write failed: {e}", flush=True)

# ─────────────────────────────────────────────────────────────────
# HTTP helpers (stdlib only — no extra dependencies needed)
# ─────────────────────────────────────────────────────────────────
def _request(method: str, path: str, headers: Optional[Dict[str, str]] = None,
             body: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
    url = API_BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return {"status": resp.status, "body": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_body = {"error": str(e)}
        return {"status": e.code, "body": err_body}
    except Exception as e:
        return {"status": -1, "body": {"error": str(e)}}

def api_post_heartbeat(bot_name: str, status: str = "up", version: Optional[str] = None,
                        container_id: Optional[str] = None, meta: Optional[Dict] = None):
    bot_key = os.environ.get("BOT_HEARTBEAT_KEY", "")
    headers = {}
    if bot_key:
        headers["X-Bot-Key"] = bot_key
    body = {
        "bot_name": bot_name,
        "status": status,
        "version": version,
        "container_id": container_id,
        "meta": meta or {},
    }
    return _request("POST", "/api/system/bots/heartbeat", headers=headers, body=body)

def api_get_pending_intents() -> List[Dict[str, Any]]:
    if not ORCHESTRATOR_KEY:
        log("ERROR", "ORCHESTRATOR_KEY env var is not set")
        return []
    r = _request("GET", "/api/system/intents/pending",
                 headers={"X-Orchestrator-Key": ORCHESTRATOR_KEY})
    if r["status"] == 200 and isinstance(r["body"], dict):
        return r["body"].get("intents", [])
    log("WARN", f"GET /intents/pending returned {r['status']}: {r['body']}")
    return []

def api_post_intent_result(intent_id: int, result: str, output: Optional[str] = None):
    return _request("POST", "/api/system/intents/result",
                    headers={"X-Orchestrator-Key": ORCHESTRATOR_KEY},
                    body={"intent_id": intent_id, "result": result, "output": output})

# ─────────────────────────────────────────────────────────────────
# Docker helpers
# ─────────────────────────────────────────────────────────────────
def run_cmd(args: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Run a shell command and return {ok, stdout, stderr, returncode}."""
    log("DEBUG", f"$ {' '.join(args)}")
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -2}

def compose_args(action: str, service: Optional[str] = None) -> List[str]:
    base = COMPOSE_CMD.split() + ["-f", COMPOSE_FILE, action]
    if service:
        base.append(service)
    return base

def docker_ps_status() -> Dict[str, str]:
    """Return {container_name: 'running'|'exited'|'restarting'|...}."""
    r = run_cmd(["docker", "ps", "-a", "--format", "{{.Names}}|{{.State}}"])
    if not r["ok"]:
        log("WARN", f"docker ps failed: {r['stderr']}")
        return {}
    out = {}
    for line in r["stdout"].splitlines():
        if "|" not in line:
            continue
        name, state = line.split("|", 1)
        out[name.strip()] = state.strip()
    return out

# ─────────────────────────────────────────────────────────────────
# Intent execution
# ─────────────────────────────────────────────────────────────────
def execute_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
    bot = intent["bot"]
    action = intent["action"]

    # Special: emergency pause for all bots
    if bot == "*" and action == "pause":
        log("WARN", "Emergency pause: stopping all expected bots")
        results = []
        for b in EXPECTED_BOTS:
            r = run_cmd(compose_args("stop", b), timeout=30)
            results.append(f"{b}: {'OK' if r['ok'] else 'FAIL'}")
        return {"result": "ok", "output": " | ".join(results)}

    if action == "restart":
        r = run_cmd(compose_args("restart", bot), timeout=60)
    elif action == "stop":
        r = run_cmd(compose_args("stop", bot), timeout=30)
    elif action == "start":
        r = run_cmd(compose_args("up", bot) + ["-d"], timeout=60)
    elif action == "pause":
        r = run_cmd(compose_args("stop", bot), timeout=30)
    elif action == "logs":
        lines = intent.get("payload", {}).get("lines", 100)
        r = run_cmd(["docker", "logs", "--tail", str(lines), f"slh-{bot.replace('-bot','')}"], timeout=30)
        return {"result": "ok" if r["ok"] else "failed", "output": r["stdout"][-3500:]}
    else:
        return {"result": "failed", "output": f"Unknown action: {action}"}

    return {
        "result": "ok" if r["ok"] else "failed",
        "output": (r["stdout"] + ("\n" + r["stderr"] if r["stderr"] else "")).strip()[:3500],
    }

# ─────────────────────────────────────────────────────────────────
# Push heartbeats for all running bot containers
# ─────────────────────────────────────────────────────────────────
def push_heartbeats():
    statuses = docker_ps_status()
    if not statuses:
        log("WARN", "No docker containers visible — is Docker running?")
        return
    pushed = 0
    for bot in EXPECTED_BOTS:
        # Container naming convention: slh-<bot-name-without-bot-suffix>
        cname = f"slh-{bot.replace('-bot', '')}"
        state = statuses.get(cname, "missing")
        if state == "running":
            api_post_heartbeat(bot, status="up", container_id=cname)
            pushed += 1
        elif state in ("restarting", "paused"):
            api_post_heartbeat(bot, status="warn", container_id=cname,
                               meta={"docker_state": state})
        else:
            api_post_heartbeat(bot, status="down", container_id=cname,
                               meta={"docker_state": state})
    # Also push for the orchestrator itself
    api_post_heartbeat("orchestrator", status="up",
                       version="1.0", meta={"pushed_for": pushed})
    log("INFO", f"Heartbeats pushed for {pushed}/{len(EXPECTED_BOTS)} running bots")

# ─────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────
def main_loop(once: bool = False, heartbeats_only: bool = False):
    log("INFO", "=" * 60)
    log("INFO", f"SLH Orchestrator starting — API: {API_BASE}")
    log("INFO", f"Poll interval: {POLL_SECONDS}s · Compose file: {COMPOSE_FILE}")
    if not ORCHESTRATOR_KEY and not heartbeats_only:
        log("ERROR", "ORCHESTRATOR_KEY env var is REQUIRED for control mode")
        log("ERROR", "Set it on Railway AND in your local .env, then restart")
        sys.exit(1)
    log("INFO", "=" * 60)

    while True:
        try:
            push_heartbeats()
            if not heartbeats_only:
                intents = api_get_pending_intents()
                for intent in intents:
                    log("INFO", f"Executing intent #{intent['id']}: {intent['action']} on {intent['bot']}")
                    result = execute_intent(intent)
                    api_post_intent_result(intent["id"], result["result"], result["output"])
                    log("INFO", f"  → {result['result']}")
        except Exception as e:
            log("ERROR", f"Loop iteration failed: {e!r}")

        if once:
            break
        time.sleep(POLL_SECONDS)

def sanity_check():
    log("INFO", "Sanity check…")
    # 1. API health
    r = _request("GET", "/api/health", timeout=10)
    if r["status"] == 200:
        log("INFO", f"  ✓ API reachable: {r['body']}")
    else:
        log("ERROR", f"  ✗ API unreachable: {r['status']} {r['body']}")
        return False
    # 2. Docker
    r = run_cmd(["docker", "--version"])
    if r["ok"]:
        log("INFO", f"  ✓ Docker: {r['stdout']}")
    else:
        log("ERROR", f"  ✗ Docker not available: {r['stderr']}")
        return False
    # 3. Compose file
    if os.path.exists(COMPOSE_FILE):
        log("INFO", f"  ✓ Compose file exists: {COMPOSE_FILE}")
    else:
        log("ERROR", f"  ✗ Compose file missing: {COMPOSE_FILE}")
        return False
    # 4. Orchestrator key
    if ORCHESTRATOR_KEY:
        log("INFO", "  ✓ ORCHESTRATOR_KEY is set")
    else:
        log("WARN", "  ⚠ ORCHESTRATOR_KEY not set (heartbeats will work, control will not)")
    log("INFO", "Sanity check complete")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SLH Orchestrator — local control layer")
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit")
    parser.add_argument("--heartbeats-only", action="store_true", help="Only push heartbeats, don't execute intents")
    parser.add_argument("--check", action="store_true", help="Sanity check and exit")
    args = parser.parse_args()

    if args.check:
        ok = sanity_check()
        sys.exit(0 if ok else 1)
    main_loop(once=args.once, heartbeats_only=args.heartbeats_only)

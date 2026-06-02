import asyncio
import os
import time
import aiohttp

RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"
RAILWAY_TOKEN   = os.getenv("RAILWAY_API_TOKEN", "")
PROJECT_ID      = os.getenv("RAILWAY_PROJECT_ID", "")
SERVICE_ID      = os.getenv("RAILWAY_SERVICE_ID", "")

RAILWAY_QUERY = """
query GetDeployments($projectId: String!, $serviceId: String) {
  deployments(
    input: {
      projectId: $projectId
      serviceId: $serviceId
    }
    first: 3
  ) {
    edges {
      node {
        id
        status
        createdAt
        staticUrl
        service {
          name
        }
      }
    }
  }
}
"""

async def check_railway() -> dict:
    if not RAILWAY_TOKEN or not PROJECT_ID:
        return {"ok": False, "status": "NOT_CONFIGURED", "detail": "RAILWAY_API_TOKEN or RAILWAY_PROJECT_ID missing"}
    variables = {"projectId": PROJECT_ID}
    if SERVICE_ID:
        variables["serviceId"] = SERVICE_ID
    headers = {"Authorization": f"Bearer {RAILWAY_TOKEN}", "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                RAILWAY_API_URL,
                json={"query": RAILWAY_QUERY, "variables": variables},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status != 200:
                    return {"ok": False, "status": "HTTP_ERROR", "detail": str(resp.status)}
                data = await resp.json()
                edges = data.get("data", {}).get("deployments", {}).get("edges", [])
                if not edges:
                    return {"ok": False, "status": "NO_DEPLOYMENTS", "detail": "No deployments found"}
                latest = edges[0]["node"]
                status = latest.get("status", "UNKNOWN")
                service_name = latest.get("service", {}).get("name", "?")
                return {
                    "ok": status == "SUCCESS",
                    "status": status,
                    "service": service_name,
                    "deploy_id": latest.get("id", "?")[:8],
                    "url": latest.get("staticUrl", ""),
                }
    except asyncio.TimeoutError:
        return {"ok": False, "status": "TIMEOUT", "detail": "Railway API timeout"}
    except Exception as e:
        return {"ok": False, "status": "ERROR", "detail": str(e)}

def check_database() -> dict:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return {"ok": False, "detail": "DATABASE_URL not set"}
    try:
        import psycopg2
        t0 = time.perf_counter()
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": True, "latency_ms": ms}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:80]}

async def check_redis() -> dict:
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return {"ok": None, "detail": "not configured"}
    try:
        import redis.asyncio as aioredis
        t0 = time.perf_counter()
        r = aioredis.from_url(redis_url, socket_timeout=3)
        await r.ping()
        await r.aclose()
        ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": True, "latency_ms": ms}
    except ImportError:
        return {"ok": None, "detail": "redis package not installed"}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:80]}

async def check_ai_key() -> dict:
    for env_var, prefix in [("ANTHROPIC_API_KEY", "sk-ant-"), ("OPENAI_API_KEY", "sk-")]:
        val = os.getenv(env_var, "")
        if val:
            valid = val.startswith(prefix)
            return {"ok": valid, "provider": env_var.split("_")[0].title(), "detail": "key present" if valid else "key format unexpected"}
    return {"ok": False, "detail": "No AI API key found"}

def _icon(result: dict) -> str:
    if result.get("ok") is True: return "✅"
    if result.get("ok") is None: return "⚪"
    return "❌"

def build_report(railway, db, redis, ai) -> str:
    lines = ["🩺 *SLH System Doctor*", "━━━━━━━━━━━━━━━━━━━━━", ""]
    r_icon = _icon(railway)
    r_status = railway.get("status", "?")
    r_service = railway.get("service", "")
    r_id = railway.get("deploy_id", "")
    lines.append(f"{r_icon} *Railway* — {r_status}")
    if r_service: lines.append(f"   service: {r_service} | deploy: {r_id}")
    if not railway["ok"] and "detail" in railway: lines.append(f"   ⚠️ {railway['detail']}")
    lines.append("")
    db_icon = _icon(db)
    if db["ok"]: lines.append(f"{db_icon} *Database* — {db.get('latency_ms', '?')}ms")
    else: lines.append(f"{db_icon} *Database* — {db.get('detail', 'error')}")
    r2_icon = _icon(redis)
    if redis.get("ok") is None: lines.append(f"{r2_icon} *Redis* — {redis.get('detail', 'skip')}")
    elif redis["ok"]: lines.append(f"{r2_icon} *Redis* — {redis.get('latency_ms', '?')}ms")
    else: lines.append(f"{r2_icon} *Redis* — {redis.get('detail', 'error')}")
    ai_icon = _icon(ai)
    ai_prov = ai.get("provider", "AI")
    lines.append(f"{ai_icon} *{ai_prov}* — {ai.get('detail', '?')}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    checks = [railway["ok"], db["ok"], ai["ok"]]
    if all(c is True for c in checks): lines.append("🟢 *All systems operational*")
    elif any(c is False for c in checks): lines.append("🔴 *Issues detected — check logs*")
    else: lines.append("🟡 *Partial — some checks skipped*")
    return "\n".join(lines)

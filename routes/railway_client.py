"""Railway GraphQL client — programmatic env-var management + redeploys.

Used by the rotation pipeline to push secrets and trigger redeploys without
relying on the Railway CLI (which is not present in production containers).

Reference:
- Public API: https://docs.railway.com/reference/public-api
- Endpoint:   https://backboard.railway.app/graphql/v2
- Auth:       Authorization: Bearer <RAILWAY_API_TOKEN> (account/workspace token)

Mutations used:
- variableUpsert(input: VariableUpsertInput!) — set env var on a service
- deploymentRedeploy(id: String!)            — redeploy a specific deployment

Queries used:
- deployments(input: DeploymentListInput!)   — get latest deployment id

The token VALUE never enters logs — every error message is sanitized via
_redact_value before being raised.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import httpx

log = logging.getLogger("slh.railway_client")

GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"
DEFAULT_TIMEOUT = 25.0


class RailwayError(RuntimeError):
    """Raised when a Railway API call fails. Token values are pre-redacted."""


def _api_token() -> str:
    tok = os.getenv("RAILWAY_API_TOKEN", "").strip()
    if not tok:
        raise RailwayError(
            "RAILWAY_API_TOKEN not set. Generate one at "
            "https://railway.com/account/tokens and set it on the slh-api service."
        )
    return tok


def _services_config_path() -> Path:
    # routes/railway_client.py → ../config/railway_services.json
    here = Path(__file__).resolve().parent
    return here.parent / "config" / "railway_services.json"


_CONFIG_CACHE: Optional[dict] = None


def load_services_config() -> dict:
    """Load + cache the env_var → Railway service mapping. Refreshed on each run."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    path = _services_config_path()
    if not path.exists():
        raise RailwayError(f"services config missing: {path}")
    try:
        _CONFIG_CACHE = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RailwayError(f"services config invalid JSON: {e}")
    if "services" not in _CONFIG_CACHE:
        raise RailwayError("services config missing top-level 'services' key")
    return _CONFIG_CACHE


def lookup_service(env_var: str) -> dict:
    """Return {project, service, environment, project_id, service_id, environment_id, tier}.

    Raises if env_var has no Railway mapping. The mapping is the source of truth
    for which Railway project + service hosts each secret.
    """
    cfg = load_services_config()
    svc = cfg["services"].get(env_var)
    if not svc:
        raise RailwayError(f"no Railway mapping for env_var={env_var}")
    required = {"project_id", "service_id", "environment_id"}
    missing = required - svc.keys()
    if missing:
        raise RailwayError(
            f"services config for {env_var} missing fields: {sorted(missing)}. "
            "Run scripts/railway_resolve_ids.py to populate them."
        )
    return svc


def _redact_value(text: str) -> str:
    """Belt-and-braces: scrub secret-shaped substrings from any string we log/raise."""
    patterns = [
        (r"\d{8,12}:[A-Za-z0-9_\-]{30,}", "<BOT_TOKEN>"),
        (r"sk-(?:ant-)?[A-Za-z0-9_\-]{20,}", "<API_KEY>"),
        (r"postgres(?:ql)?://[^@]+@[^/\s]+/\S+", "postgres://<REDACTED>"),
        (r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "<JWT>"),
    ]
    for pat, repl in patterns:
        text = re.sub(pat, repl, text)
    return text


async def _graphql(query: str, variables: dict, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Low-level GraphQL POST. Returns `data` block. Raises RailwayError on errors."""
    token = _api_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"query": query, "variables": variables}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(GRAPHQL_URL, headers=headers, json=payload)
    except httpx.RequestError as e:
        raise RailwayError(f"network error talking to Railway: {type(e).__name__}")
    if r.status_code != 200:
        body = _redact_value(r.text[:500])
        raise RailwayError(f"Railway HTTP {r.status_code}: {body}")
    try:
        data = r.json()
    except Exception:
        raise RailwayError(f"Railway non-JSON response: {_redact_value(r.text[:300])}")
    if "errors" in data and data["errors"]:
        first = data["errors"][0]
        msg = _redact_value(str(first.get("message", first))[:400])
        raise RailwayError(f"Railway GraphQL error: {msg}")
    return data.get("data") or {}


# ─── Public API ────────────────────────────────────────────────────────────


async def variable_upsert(
    env_var: str,
    new_value: str,
    *,
    skip_deploys: bool = True,
) -> dict:
    """Push a new value for `env_var` to its mapped Railway service.

    skip_deploys=True (default) means Railway will NOT auto-redeploy on this set —
    we trigger redeploy explicitly via service_redeploy() so the pipeline can
    sequence audit-log + healthcheck around it. Set False if you want Railway's
    built-in auto-redeploy.
    """
    svc = lookup_service(env_var)
    query = """
    mutation variableUpsert($input: VariableUpsertInput!) {
      variableUpsert(input: $input)
    }
    """
    variables = {
        "input": {
            "projectId": svc["project_id"],
            "environmentId": svc["environment_id"],
            "serviceId": svc["service_id"],
            "name": env_var,
            "value": new_value,
            "skipDeploys": skip_deploys,
        }
    }
    await _graphql(query, variables)
    return {
        "ok": True,
        "env_var": env_var,
        "service": svc.get("service"),
        "project": svc.get("project"),
    }


async def latest_deployment_id(env_var: str) -> Optional[str]:
    """Return the most recent successful deployment id for env_var's service."""
    svc = lookup_service(env_var)
    query = """
    query latestDeployment($input: DeploymentListInput!) {
      deployments(input: $input, first: 1) {
        edges { node { id status createdAt } }
      }
    }
    """
    variables = {
        "input": {
            "projectId": svc["project_id"],
            "serviceId": svc["service_id"],
            "environmentId": svc["environment_id"],
        }
    }
    data = await _graphql(query, variables)
    edges = (data.get("deployments") or {}).get("edges") or []
    if not edges:
        return None
    return edges[0]["node"]["id"]


async def service_redeploy(env_var: str) -> dict:
    """Trigger a redeploy of the service hosting env_var.

    Resolves the latest deployment id and redeploys it. Returns the new deploy
    id + status.
    """
    deploy_id = await latest_deployment_id(env_var)
    if not deploy_id:
        raise RailwayError(
            f"no deployments found for service hosting {env_var} — "
            "is the service freshly created?"
        )
    query = """
    mutation deploymentRedeploy($id: String!) {
      deploymentRedeploy(id: $id) { id status }
    }
    """
    data = await _graphql(query, {"id": deploy_id})
    result = data.get("deploymentRedeploy") or {}
    return {
        "ok": True,
        "deploy_id": result.get("id") or deploy_id,
        "status": result.get("status"),
        "env_var": env_var,
    }


async def health_probe() -> dict:
    """Verify the API token works. Used at startup + by /api/admin/rotation-history."""
    query = "query { me { id email } }"
    try:
        data = await _graphql(query, {})
        me = data.get("me") or {}
        return {"ok": True, "me_id": me.get("id"), "me_email": me.get("email")}
    except RailwayError as e:
        return {"ok": False, "error": str(e)}

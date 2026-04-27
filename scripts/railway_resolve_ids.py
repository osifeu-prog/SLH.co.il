"""Resolve Railway project/service/environment IDs for config/railway_services.json.

Usage (once, after `RAILWAY_API_TOKEN` is set locally):
    cd D:\\SLH_ECOSYSTEM
    python scripts/railway_resolve_ids.py            # dry-run, prints diff
    python scripts/railway_resolve_ids.py --write    # writes back to JSON

What it does:
    1. Queries Railway GraphQL for all projects the token can see.
    2. For each entry in config/railway_services.json with empty IDs,
       matches by `project` (project name) + `service` (service name) +
       `environment` (env name) and fills the IDs.
    3. Reports unresolved entries — these need manual fix (typically a
       project/service rename mismatch between the JSON and Railway).

Token required: RAILWAY_API_TOKEN with read scope on the workspace.
Get one: https://railway.com/account/tokens

This is read-only against Railway. The only write is to the local JSON file
(behind --write). Safe to run repeatedly.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "railway_services.json"

WORKSPACE_QUERY = """
query workspaceProjects {
  me {
    workspaces {
      id name
      team {
        id name
        projects {
          edges {
            node {
              id name
              services { edges { node { id name } } }
              environments { edges { node { id name } } }
            }
          }
        }
      }
    }
    projects {
      edges {
        node {
          id name
          services { edges { node { id name } } }
          environments { edges { node { id name } } }
        }
      }
    }
  }
}
"""


async def fetch_projects(token: str) -> list[dict]:
    """Return [{name, id, services: {name: id}, environments: {name: id}}]."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(GRAPHQL_URL, headers=headers, json={"query": WORKSPACE_QUERY})
    if r.status_code != 200:
        raise RuntimeError(f"Railway HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError(f"Railway GraphQL: {data['errors'][0].get('message')}")

    me = data["data"]["me"]
    projects: list[dict] = []

    def _flatten_proj_edge(edge: dict) -> dict:
        node = edge["node"]
        return {
            "id": node["id"],
            "name": node["name"],
            "services": {s["node"]["name"]: s["node"]["id"] for s in node.get("services", {}).get("edges", [])},
            "environments": {e["node"]["name"]: e["node"]["id"] for e in node.get("environments", {}).get("edges", [])},
        }

    # Personal projects on me.projects
    for edge in (me.get("projects") or {}).get("edges") or []:
        projects.append(_flatten_proj_edge(edge))

    # Workspace/team projects
    for ws in me.get("workspaces") or []:
        team = ws.get("team") or {}
        for edge in (team.get("projects") or {}).get("edges") or []:
            projects.append(_flatten_proj_edge(edge))

    # De-dupe by id
    seen = set()
    uniq = []
    for p in projects:
        if p["id"] not in seen:
            seen.add(p["id"])
            uniq.append(p)
    return uniq


def resolve_entry(entry: dict, projects: list[dict]) -> tuple[bool, str]:
    """Mutate entry in place. Returns (changed?, message)."""
    proj_name = entry.get("project")
    svc_name = entry.get("service")
    env_name = entry.get("environment", "production")
    if not proj_name or not svc_name:
        return False, "missing project/service in JSON"

    proj = next((p for p in projects if p["name"].lower() == proj_name.lower()), None)
    if not proj:
        return False, f"project '{proj_name}' not found in workspace"

    svc_id = proj["services"].get(svc_name) or next(
        (sid for sname, sid in proj["services"].items() if sname.lower() == svc_name.lower()),
        None,
    )
    env_id = proj["environments"].get(env_name) or next(
        (eid for ename, eid in proj["environments"].items() if ename.lower() == env_name.lower()),
        None,
    )

    if not svc_id:
        return False, f"service '{svc_name}' not found in project '{proj_name}'"
    if not env_id:
        return False, f"environment '{env_name}' not found in project '{proj_name}'"

    changed = False
    if entry.get("project_id") != proj["id"]:
        entry["project_id"] = proj["id"]
        changed = True
    if entry.get("service_id") != svc_id:
        entry["service_id"] = svc_id
        changed = True
    if entry.get("environment_id") != env_id:
        entry["environment_id"] = env_id
        changed = True
    return changed, "ok"


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="Write resolved IDs back to JSON")
    args = ap.parse_args()

    token = os.getenv("RAILWAY_API_TOKEN", "").strip()
    if not token:
        print("ERROR: RAILWAY_API_TOKEN not set. Get one at https://railway.com/account/tokens",
              file=sys.stderr)
        sys.exit(2)

    print(f"Loading {CONFIG_PATH}...")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    print("Fetching Railway projects/services/environments...")
    projects = await fetch_projects(token)
    print(f"  Found {len(projects)} projects in workspace:")
    for p in projects:
        print(f"    - {p['name']:<30} ({len(p['services'])} services, {len(p['environments'])} envs)")
    print()

    changed_count = 0
    unresolved = []
    for env_var, entry in cfg["services"].items():
        if env_var.startswith("_"):
            continue
        changed, msg = resolve_entry(entry, projects)
        if msg != "ok":
            unresolved.append((env_var, msg))
        elif changed:
            changed_count += 1
            print(f"  ✓ resolved {env_var:<28} → {entry['project']}/{entry['service']}/{entry['environment']}")

    print()
    print(f"Resolved: {changed_count} entries")
    if unresolved:
        print(f"Unresolved: {len(unresolved)} entries — fix project/service names in JSON:")
        for env_var, msg in unresolved:
            print(f"  ✗ {env_var:<28} {msg}")

    if args.write:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nWrote {CONFIG_PATH}")
    else:
        print("\nDry-run only. Re-run with --write to persist.")


if __name__ == "__main__":
    asyncio.run(main())

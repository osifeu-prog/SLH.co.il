# Legacy api/routes â€” archived 2026-04-20

## What this is

A stale mirror of the FastAPI route modules that used to live at `D:/SLH_ECOSYSTEM/api/routes/`. Moved here on 2026-04-20 (Night 20.4 late cleanup).

**22 Python modules** â€” last meaningful edit 2026-04-17. Never re-synced after the `/routes/` top-level directory became the canonical source of truth.

## Why it was archived

At the time of the move:

- **Nothing imported these modules.** Grep across the entire `D:/SLH_ECOSYSTEM/` tree:
  - `from api.routes` â€” 0 matches
  - `import api.routes` â€” 0 matches
  - `api.routes.` â€” 0 matches
- **Nothing executed `api/main.py`** (which uses `from routes.X import â€¦`, so if run from the `api/` directory it would resolve to `api/routes/`):
  - Root `Procfile`, `Dockerfile`, `railway.json` â†’ run `uvicorn main:app` against **root** `main.py`.
  - `api/Procfile`, `api/Dockerfile`, `api/railway.json` exist but are not referenced by Railway (Railway uses the root config) and are not referenced by any docker-compose service or local script.
- **`api/main.py` is actually broken as a standalone entrypoint.** It imports `routes.admin_rotate` and `routes.bot_registry`, neither of which existed under `api/routes/`. These exist only in the canonical `/routes/` directory.
- **Security pollution, not live risk.** 8 files held a hardcoded `"slh2026admin"` fallback (broadcast, campaign_admin, creator_economy, payments_auto, pancakeswap_tracker, aic_tokens, agent_hub, treasury). Because the code never ran, the fallback was unreachable â€” but it kept showing up in grep-based security audits and muddying reviews.

The canonical active routes are at `D:/SLH_ECOSYSTEM/routes/` (24 modules including `admin_rotate.py` and `bot_registry.py`). That directory is clean.

Full context: `D:/SLH_ECOSYSTEM/ops/NIGHT_20260420_LATE_OUTCOMES.md` â†’ section **Tier B #11**.

## Rollback

If anything starts failing and you suspect this directory was actually needed:

```bash
# Put it back exactly where it was
mv D:/SLH_ECOSYSTEM/archive/legacy_api_routes_20260420 D:/SLH_ECOSYSTEM/api/routes
```

No git operations required â€” the move was local-only and not committed.

If you decide to keep the archive out of the tree permanently, you can delete this directory â€” but first `grep -r "api.routes" D:/SLH_ECOSYSTEM/` once more to confirm nothing new started importing from it.

## What was verified before the move

| Check | Result |
|---|---|
| `grep "from api.routes"` | 0 matches |
| `grep "import api.routes"` | 0 matches |
| `grep "api\.routes\."` | 0 matches |
| `api/main.py` referenced in Procfile / Dockerfile / railway.json (root or api/) | No |
| `api/main.py` referenced in docker-compose.yml | No |
| `api/main.py` referenced in any `.ps1` / `.sh` / `.bat` | No |
| `api/main.py` imports match modules present in `api/routes/` | No (admin_rotate + bot_registry missing) |

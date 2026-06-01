# SLH System Supervisor Rules
## Enforced from Session 10+ (13 April 2026)

### Before ANY Production Change:
1. `python -c "import py_compile; py_compile.compile('api/main.py', doraise=True)"` — SYNTAX CHECK
2. `cp api/main.py main.py` — SYNC ROOT
3. `diff main.py api/main.py` — VERIFY IDENTICAL
4. `git add + commit + push` — DEPLOY
5. Wait 90s → `curl /api/health` — VERIFY LIVE
6. Test affected endpoints — VALIDATE

### NEVER:
- Push without syntax check
- Change bot tokens without backup
- Delete DB tables without snapshot
- Deploy unverified code to Railway

### ALWAYS:
- Log to ops/overnight-health-log.md
- Update SESSION_HANDOFF after major changes
- Keep CLAUDE.md current
- Real data only — no mocks in production

### Deployment Chain:
```
api/main.py (source of truth)
    ↓ cp
main.py (Railway builds from here)
    ↓ git push
Railway auto-deploy
    ↓ verify
/api/health → 200 OK
```

### Token Economy Rules:
- SLH = premium (never give free beyond Genesis rewards)
- ZVK = activity rewards (controlled amounts)
- MNH = stablecoin (1:1 ILS)
- REP = reputation (earned, not bought)
- ZUZ = risk signal ONLY (not currency, not tradeable)

### Security Gates:
- [ ] JWT_SECRET set on Railway
- [ ] ADMIN_API_KEYS overridden
- [ ] No passwords in public HTML
- [ ] .env tokens rotated

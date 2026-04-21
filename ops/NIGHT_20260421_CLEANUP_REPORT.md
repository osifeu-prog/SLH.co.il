# Night 21.4 — D:\ Cleanup Report

**Date:** 2026-04-21 (completed ~10:52 local)
**Operator:** Claude Opus 4.7
**Method:** move-only, never delete (reversible)

## Result

| Metric | Before | After | Δ |
|--------|--------|-------|---|
| `D:\` root entries | 125 | **48** | -77 (-62%) |
| Items archived | 0 | **79** | +79 |
| Docker containers running | 22 | **22** | 0 (all healthy) |
| `/api/health` | 200 OK | **200 OK** | no change |
| Live systems harmed | — | **0** | — |

## Archive layout
`D:\_ARCHIVE_2026-04-21\`
- `zips/` — 17 items (backup zips, audit zips, trust verification)
- `old_audits/` — 18 items (dated audit/diagnostic dirs + SLH_REAL_SYSTEM + generic audits)
- `old_backups/` — 3 items (SLH_BACKUPS, SLH_SAFE_BACKUPS, ARCHIVE_SLH_OLD)
- `loose_scripts/` — 41 items (fix_*, check_*, tmp_*, diag_*, find_*, test*, rebuild_*)

Full ledger: `D:\_ARCHIVE_2026-04-21\MOVE_LOG.txt` — every move logged with source and destination.

## What was explicitly NOT moved (protected)

**Live production:**
- `SLH_ECOSYSTEM` (main Railway stack, 22 bots)
- `SLH_BNB` (separate investor system)
- `SLH_CONTROL.ps1` (orchestrator)

**Hebrew-flagged by user ("לא למחוק"):**
- `אתר ובוט מחובר לבייננס - לא למחוק.zip`
- `מחובר ל BNB למשקיעים לא למחוק (בוטפאקטורי).zip`

**Labs / apps / dormant bots:**
- `AISITE`, `SLH_GAME_TEST`, `SLHWallet`, `SLH_APP`
- `SLH_AGENT_MERCHANT`, `SLH_AGENT_SALES`, `SLHB`, `GATE_BOTSHOP`, `ExpertNet_Core`, `GAMES`
- `guardian-enterprise`, `telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`

**Unknown / deferred (need user review):**
- `BOT_FACTORY.zip`, `HBD.zip`, `GATE_BOTSHOP-main (2).zip`, `campaign.zip`, `campaign1*`
- `SLH`, `SLHSITE`, `SLH_SECURE`, `44`, `T`, `tmp`, `WALLETTG`
- `app`, `Gardient2_Final`, `ReactProjects`, `DockerData`, `Dockerfile`
- `compose.yaml`, `compose.debug.yaml` (skeleton — image: image template, likely orphaned but left for user)
- `campaign-483518-1baa49543928.json` (Google service account — never touched)
- `.xlsx`, `.txt` office files

## Verification (post-cleanup)

```bash
$ docker ps --format '{{.Names}}' | wc -l
22

$ curl -sS https://slh-api-production.up.railway.app/api/health
{"status":"ok","db":"connected","version":"1.1.0"}
```

## Reversal

Any single item:
```bash
mv "/d/_ARCHIVE_2026-04-21/<category>/<name>" "/d/<name>"
```

Full reversal:
```bash
mv /d/_ARCHIVE_2026-04-21/zips/* /d/
mv /d/_ARCHIVE_2026-04-21/old_audits/* /d/
mv /d/_ARCHIVE_2026-04-21/old_backups/* /d/
mv /d/_ARCHIVE_2026-04-21/loose_scripts/* /d/
rmdir /d/_ARCHIVE_2026-04-21/*
rmdir /d/_ARCHIVE_2026-04-21
```

## What's left for user review

48 items remain at `D:\` root. The **unknown / deferred** list above (~20 items) should be reviewed by you at leisure — each needs a 10-second "is this live/important?" judgement. No rush.

After user confirmation of those, a follow-up pass can reduce root to ~25 entries (live systems + labs + SLH_CONTROL.ps1 + `_ARCHIVE_2026-04-21` + Hebrew-flagged zips).

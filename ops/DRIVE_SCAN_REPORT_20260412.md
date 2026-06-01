# Drive Scan Report — D:\SLH_* Inventory

**Date:** April 12, 2026
**Scanner:** Automated overnight agent (Claude Opus 4.6)
**Scope:** All `D:\SLH*` folders + related projects

## Summary

| Category | Count |
|----------|-------|
| **Active Projects** | 3 |
| **Duplicates (can archive)** | 2 |
| **Empty / Unused** | 6 |
| **Audit / Diagnostic Dumps** | 11 |
| **Backup ZIPs (cold storage)** | 9 |

---

## 🟢 Active & Strategic Projects

### 1. `D:\SLH_ECOSYSTEM` ← MAIN (already in use)
- **Status:** Production-grade integrated platform
- **Contents:** 22+ Telegram bots, FastAPI backend, static website (GitHub Pages), shared libs
- **Git:** Tracked
- **Last Modified:** 2026-04-11
- **Note:** Docker Compose with PostgreSQL + Redis. **This is your single source of truth.**

### 2. `D:\SLH_PROJECT_V2` ← **ACTIVE SEPARATE BACKEND** ⚠️
- **Status:** Primary bot backend for "SLH Academia", **production-live on Railway**
- **Contents:** aiogram Python bot, webhook/worker architecture, financial ledger system
- **Git:** Tracked (github.com/osifeu-prog/SLH_PROJECT_V2.git)
- **Last Modified:** 2026-04-09
- **Target:** 100K+ users
- **⚠️ IMPORTANT:** This is **NOT a backup** — it's an active Railway service separate from SLH_ECOSYSTEM. Earlier it caused the NFTY token conflict when running alongside `slh-nfty` container.
- **RECOMMENDATION:** Audit what's running here vs. SLH_ECOSYSTEM. Either:
  - Consolidate into SLH_ECOSYSTEM (recommended for single source of truth)
  - Or formally document the split and ensure no bot token conflicts

### 3. `D:\SLH` (React Native CryptoWallet — WIP)
- **Status:** Incomplete mobile wallet app
- **Contents:** TypeScript/React Native, Android/iOS configs, QR code integration
- **Last Modified:** 2026-02-08
- **Integration Opportunity:** Could merge with SLH_ECOSYSTEM's web3.js layer and become the mobile companion app for slh-nft.com
- **Effort estimate:** Medium (2-5 days) — mostly build/iOS provisioning work

---

## 🟡 Duplicates (can archive)

### `D:\SLH_AGENT_MERCHANT`
- Symbolic copy of SLH_PROJECT_V2
- No unique code
- **Action:** Archive or delete

### `D:\SLH_AGENT_SALES`
- Symbolic copy of SLH_PROJECT_V2
- Only contains state docs + project briefs pointing to main
- **Action:** Archive or delete

---

## 🔵 Empty / Unused Folders

### `D:\SLHB` (Python bot template)
- Basic aiogram boilerplate with user registration + XP skeleton
- **Use case:** Reference template for new bots (already replicated in SLH_ECOSYSTEM patterns)
- **Action:** Keep as reference, no integration needed

### `D:\SLHWallet`
- Empty React Native infrastructure
- No production code
- **Action:** Archive

### `D:\SLHSITE`
- Empty placeholder
- **Action:** Delete

### `D:\SLH_APP`
- TypeScript app skeleton — only stubs (wallet.ts, points.ts, api.ts)
- Contains a 3.9MB diagnostic scan file
- **Action:** Archive

### `D:\SLH_BNB`, `D:\SLH_BOTS`, `D:\SLH_CONTROL`
- Virtual environment directories only (venv/, no source)
- **Action:** Delete — these are pip install dirs

---

## ⚪ Audit / Diagnostic Snapshots (no action)

These are historical snapshots from previous debugging sessions. Keep for forensic reference, don't integrate:

1. `SLH_AUDIT_2026-04-09` — API health checks
2. `SLH_AUDIT_FULL` — Full ecosystem audit
3. `SLH_AUDIT_NIFTII` — NFTI bot audit
4. `SLH_DIAGNOSTICS_20260411_190125` — Latest runtime diagnostics
5. `SLH_DIAG_20260410_120427` — Previous
6. `SLH_HOTFIX_BACKUP_20260409_215251` — Backup from hotfix session
7. `SLH_LIVE_VERIFY_20260411_192534` — Latest verification
8. `SLH_RESTORE_20260410_011044` — Restore point
9. `SLH_SYNC_CHECK_20260409` — Sync validation
10. `SLH_WALLET_E2E_AUDIT_20260409` — E2E test audit
11. `SLH_SAFE_BACKUPS` + `SLH_BACKUPS` — Backup directories

---

## 📦 Backup ZIPs (cold storage candidates)

| File | Size | Age |
|---|---|---|
| SLH_BACKUP_2026-03-05_12-51.zip | 6.5 KB | 37 days |
| SLH_BACKUP_AUTO_2026-03-05_12-54.zip | 7.4 KB | 37 days |
| SLH_BACKUP_AUTO_2026-03-05_12-59.zip | 21.6 KB | 37 days |
| SLH_BACKUP_AUTO_2026-03-05_13-01.zip | 21.9 KB | 37 days |
| SLH_BACKUP_SUCCESS_2026-03-05_12-53.zip | 6.7 KB | 37 days |
| SLH_PROJECT_V2_BACKUP.zip | 119 KB | varies |
| SLH_PROJECT_V2_snapshot_20260331_201602.zip | 706 KB | 12 days |
| SLH_PROJECT_V2_snapshot_20260331_204647.zip | 706 KB | 12 days |
| SLH_DIAGNOSTICS_20260411_190125.zip | 27 KB | 1 day |

**Recommendation:** Move all backups >30 days old to `D:\SLH_BACKUPS\cold-storage\`.

---

## 🔑 Key Insights

### Hidden Feature Found
**SLH_PROJECT_V2** contains a **fully functional ledger-backed finance system with 10-generation referral tracking**. This is the heart of the SLH Academia platform and is already in production on Railway.

**Question for you:** Is this the same code as what's in `SLH_ECOSYSTEM/api/main.py` or a separate codebase? If separate, they may be duplicating work.

### Integration Opportunities
1. **`D:\SLH`** (React Native wallet) → merge into SLH_ECOSYSTEM mobile offering
2. **`SLH_PROJECT_V2`** → consolidate into SLH_ECOSYSTEM or formally document split

### Safe to Clean Up
- 6 empty/duplicate folders (no code loss)
- 9 backup ZIPs older than 30 days
- Potential to free ~10MB of disk + significant mental clutter

---

## Recommended Action Plan

### Today (5 minutes)
- [ ] Archive `SLH_AGENT_MERCHANT` + `SLH_AGENT_SALES` (clear duplicates)
- [ ] Delete empty: `SLHSITE`, `SLH_BNB`, `SLH_BOTS`, `SLH_CONTROL`

### This week (30 minutes)
- [ ] Move all backup ZIPs to `D:\SLH_BACKUPS\cold-storage\`
- [ ] Archive `SLH_APP`, `SLHWallet`
- [ ] Decide: keep `SLHB` as reference template or archive

### This month (2-5 days, if business priority)
- [ ] Investigate `SLH_PROJECT_V2` vs `SLH_ECOSYSTEM` overlap — consolidate
- [ ] Finish `D:\SLH` React Native wallet → integrate with slh-nft.com

---

**Overall:** `SLH_ECOSYSTEM` is clearly your active production codebase. Everything else is either a duplicate, historical snapshot, or experimental WIP. No immediate risk, but significant mental/disk clutter.

*Generated by overnight drive scan agent — 2026-04-12*

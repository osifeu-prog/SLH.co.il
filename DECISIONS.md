# DECISIONS.md  SLH Spark AI

## 2026-06-03: Source of Truth (SSoT)
- **Decision:** ot_stable_last_working.py (commit c851892) is the official version.
- **Reason:** The file is running in production (deployment 777c2717), passes syntax check, and contains most basic features.
- **Alternatives considered:** ot_backup_final.py was rejected due to secrets_local dependency and BOM issues.

## 2026-06-03: Configuration Source
- **Decision:** Use Railway environment variables exclusively.
- **Variables:** BOT_TOKEN, DATABASE_URL, GROQ_API_KEY, ADMIN_TELEGRAM_IDS, TON_WALLET.
- **Reason:** Eliminate dependency on secrets_local.py to prevent ModuleNotFoundError in Railway.

## 2026-06-03: Architecture Principle
- **Decision:** Feature‑based modular architecture (core / services / features / shared).
- **Reason:** Reduce regressions, isolate functionality, and enable independent development of features.

## 2026-06-03: Freeze List (until mapping complete)
- ❄️ ot_stable_last_working.py (local copy)
- ❄️ Deployment 777c2717 (production)
- ❄️ Existing PostgreSQL tables (read‑only)
- ❄️ Environment variables (read‑only)

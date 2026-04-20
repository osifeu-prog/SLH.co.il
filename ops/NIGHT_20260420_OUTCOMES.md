# 🌙 Night 20.4.2026 · Outcomes Report
**Session:** 2026-04-20 afternoon→evening · **Agent:** Claude Opus 4.7 (1M context)
**Commits:** `ed81daf` (slh-api), `9ab68f6` (website)

---

## ✅ DONE

### 🌱 Seed content (3/3 streams)

| Stream | Action | Status | Live? |
|---|---|---|---|
| Academia | Registered Osif as instructor #1 | `pending` — needs admin approve | no |
| Marketplace | Listed 5 items as seller 224223270 | all auto-approved ✅ | **YES** |
| Experts | Draft template prepared | awaiting Osif input | no |

**Marketplace items LIVE on `/api/marketplace/items`:**
| id | title | price | currency |
|---|---|---|---|
| 1 | ייעוץ 1:1 — שעה עם Osif (bot dev) | 199 | ILS |
| 2 | Custom Telegram Bot Setup (turnkey) | 499 | SLH |
| 3 | SLH API Sandbox Access (30 days) | 49 | ILS |
| 4 | Hebrew Crypto Starter Pack (PDF+Discord) | 39 | ILS |
| 5 | SLH Spark Membership Pack (sticker+badge) | 19 | ILS |

**Drafts in** `ops/SEED_CONTENT_PROPOSAL_20260420.md` — awaiting your review:
- 3 academia courses (bot bootcamp, SLH guide, crypto wallet)
- 2 expert templates (need Tzvika + Zohar info)

---

### 🔑 Admin key rotation system (full feature, LIVE)

**Backend — new module `routes/admin_rotate.py`:**
- `POST /api/admin/rotate-key` · requires current admin, takes new_key + optional label
- `GET  /api/admin/key-status` · returns last rotation info (no keys exposed)
- `POST /api/admin/reload-keys` · force in-memory cache refresh
- New table `admin_secrets` (key_hash, salt, label, active, created_at, rotated_at, created_by)
- SHA-256 + per-key random salt hashing (same pattern as `hash_admin_password`)
- In-memory cache of active DB keys → **no DB hit per admin request** (perf)
- Additive to env `ADMIN_API_KEYS` (backward compat — env keys still work)

**`_require_admin` patched** in `api/main.py` line 142:
1. env key match → OK
2. DB key match (via `check_db_admin_key`) → OK
3. JWT → OK
4. else 403

**Frontend — `admin.html` / ניהול אדמינים page:**
- New 🔑 שינוי ססמת מערכת section (red-bordered, below "Add new admin")
- Status box: shows active DB key + last rotation time
- 🎲 random generator (24-char urlsafe, Web Crypto API)
- 12+ char + 2-class strength validation (client + server)
- Confirm-password flow
- On success: updates `localStorage.slh_admin_password` automatically

**How to use:**
1. Go to `/admin.html` → "ניהול אדמינים" (sidebar)
2. Scroll to "🔑 שינוי ססמת מערכת"
3. Click 🎲 for random OR type your own (12+ chars)
4. Confirm + click "🔄 רוטציה עכשיו"
5. localStorage updates → keep working with new key
6. To fully retire env keys, remove from Railway `ADMIN_API_KEYS` (separate step)

---

### 🧹 `slh2026admin` purge (10 files)

Previously: 10 Python modules had `os.getenv("ADMIN_API_KEYS", "slh2026admin")` — public-source fallback let anyone bypass auth if Railway env was unset.

**Fixed (all 10):**
- `api/main.py` — removed `_ADMIN_KEYS_DEFAULT` hardcoded set
- `api/main.py` line 8042 admin_users seed — now uses `os.getenv("INITIAL_ADMIN_PASSWORD", "change_me_on_first_login_" + random)`
- `routes/academia_ugc.py`, `agent_hub.py`, `aic_tokens.py`, `bot_registry.py`, `broadcast.py`, `campaign_admin.py`, `creator_economy.py`, `pancakeswap_tracker.py`, `payments_auto.py`, `treasury.py` — all `"slh2026admin"` → `""` (fail-safe)
- `ops/api-health-check.py` — reads `SLH_ADMIN_KEY` env var

**Net effect:** if Railway `ADMIN_API_KEYS` is ever dropped, admin access silently fails 403 instead of falling back to a publicly-known key.

---

### 🛰️ Deployed

| Repo | Commit | Branch | Target | Status |
|---|---|---|---|---|
| slh-api | `ed81daf` | master | Railway | ✅ live — `/api/admin/key-status` returns 403 on no auth (correct) |
| osifeu-prog.github.io | `9ab68f6` | main | GitHub Pages | ✅ pushed — CDN propagation ~1-3 min |

**verify_slh.py:** 11/12 pass (same as baseline — 1 unrelated `runtime_status_fresh` fail)

---

## ⚠️ FLAGGED (needs your attention)

### 1. Payment timeout `ACAD-8789977826-1-1776686819` · **RESOLVED**
**Verdict:** user 8789977826 did **NOT** pay. No action needed.

- Queried `academy_licenses` directly via docker exec — 0 rows for user_id 8789977826
- They clicked "buy" at 15:06 UTC → got TON instructions → never sent TON → 10-min timeout fired
- No money lost, no license owed

**Bug side-effect:** the timeout message pointed them at `@SLHSupport` (handle doesn't exist). Already fixed in `docker-compose.yml` (`SUPPORT_HANDLE=@osifeu_prog`), container restarted at 15:14 UTC, verified via `docker exec slh-academia-bot env`. Future errors will show the correct handle.

### 2. Only 1 course exists: `[DEMO] מבוא ל-SLH` (49₪, id=1) · UX problem
`academy_courses` table has exactly 1 row — the seed course from `academia-bot/bot.py:94`. It's **active=TRUE** so users can attempt to buy it, but it has no `instructor_id` and no `approval_status='approved'`, so the UGC API `/api/academia/courses` returns 0 (filters on UGC schema only).

**Two paths forward (pick one post-admin-key):**
- **A. Promote to real:** attach to instructor #1 (Osif), set `approval_status='approved'`, rename (remove `[DEMO]`). Requires real materials_url.
- **B. Deactivate:** `UPDATE academy_courses SET active=FALSE WHERE id=1` — hides from bot, blocks future confused purchases until real courses exist.

Both are SQL one-liners. Tell me which path after rotation.

### 2. Academia instructor #1 still pending
I registered you but can't approve without admin key (I got 403 on all admin calls — Railway env is set to a key I don't have).

**After rotation** (or if you share the current key): run the approval chain:
```bash
# Replace $KEY with your current or post-rotation admin key
curl -X POST https://slh-api-production.up.railway.app/api/academia/instructor/approve \
  -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"instructor_id":1,"approved":true}'
```

Then you can create the 3 courses from the proposal file.

### 3. Experts seed — still blocked on your info
Need 5 fields per expert (Tzvika + Zohar): display_name, tg_username, bio, linkedin/website, domains, years_experience.

---

## 🔒 Security posture · before vs after

| Attack vector | Before | After |
|---|---|---|
| Source code leak → bypass admin | 🔴 `slh2026admin` fallback worked | 🟢 fail-safe empty (must have env or DB key) |
| Stolen Railway env → permanent takeover | 🔴 must rotate via dashboard | 🟡 can rotate via UI in 10 sec |
| Lost admin key | 🔴 deploy change needed | 🟢 rotate in UI, env key still works as recovery |
| Brute-force `X-Admin-Key` | 🟡 fixed 4 keys | 🟢 SHA-256 + 16-byte salt per DB key |

---

## 📊 Revenue channel status (post-seed)

| # | Channel | Before 20.4 | After 20.4 | Δ |
|---|---|---|---|---|
| 1 | Premium subscription | 🟢 LIVE (12 premium) | 🟢 LIVE | — |
| 2 | Academia UGC | 🔴 DORMANT | 🟡 READY (instructor registered, 0 approved courses) | +1 step |
| 3 | Marketplace | 🟡 READY (0 items) | **🟢 LIVE (5 items approved)** | +3 items |
| 4 | Experts | 🟡 READY (1 expert unverified) | 🟡 READY (still 1) | — |
| 7 | Staking | 🟢 LIVE (small) | 🟢 LIVE | — |

**Marketplace moved from READY → LIVE** — if any of the 280 users buys, revenue flows.

---

## 🔌 Ready-to-run seed scripts (post-admin-key)

Both live in `ops/`. Syntax-checked. Idempotent where possible.

**`ops/SEED_ACADEMIA_RUN.sh`** — approves instructor #1 + creates 3 courses + approves them.
```bash
export ADMIN_KEY='your-key-after-rotation'
bash ops/SEED_ACADEMIA_RUN.sh
```

**`ops/SEED_EXPERTS_RUN.sh`** — registers Tzvika + Zohar as experts + approves both.
Edit the TZVIKA_* and ZOHAR_* vars at top first (name, tg_username, bio, linkedin, domains).
```bash
# After filling in bio fields in the file:
export ADMIN_KEY='your-key-after-rotation'
bash ops/SEED_EXPERTS_RUN.sh
```

---

## 🖥️ Visual verification (this session)
- `/gallery.html` serves 5 items from Railway — rendered in local preview: title + price + category + seller ID all correct
- `/admin.html` — "🔑 שינוי ססמת מערכת (X-Admin-Key)" section renders; rotate + generate buttons present; status box says "⚠️ לא מחובר" when auth is fake (expected behavior)
- Live GitHub Pages propagation confirmed via `curl https://slh-nft.com/admin.html | grep "רוטציה עכשיו"` → 1 match
- academia-bot: `docker exec` confirms SUPPORT_HANDLE env is now `@osifeu_prog`

---

## 🎯 Next session priorities

1. **Rotate admin key via new UI** (2 min) — proves rotation works end-to-end
2. **Approve instructor #1 + create 3 courses** (15 min with admin key)
3. **Onboard Tzvika + Zohar as experts** (20 min — you provide info, I call API)
4. **Marketing push** to the 280 users about the 5 new marketplace items (not automated broadcast — hand-pick first 20 to avoid spam flag)
5. **Look into payment verification bug** — why did ACAD-8789977826-1-1776686819 time out?

---

## 📎 Artifacts this session

- `routes/admin_rotate.py` (new, 240 lines)
- `api/main.py` + `main.py` (synced, 5 edits)
- 10 route modules (`slh2026admin` purged)
- `website/admin.html` (new section + 3 JS functions, 93 lines added)
- `ops/SEED_CONTENT_PROPOSAL_20260420.md` (drafts for your review)
- `ops/NIGHT_20260420_OUTCOMES.md` (this file)

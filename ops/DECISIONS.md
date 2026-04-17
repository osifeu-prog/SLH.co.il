# 🧭 SLH Decision Log
> **Persistent decisions we DON'T revisit.** Append-only. Each decision has: date, context, decision, rationale, status.
> If you want to reverse a decision — add a NEW entry explaining why. Don't delete.

---

## 2026-04-17

### D-005 — Telegram group as central log + gated user access (02:30)
**Context:** User has a Telegram group with most of the bots already in it. Users are NOT yet invited.

**Decision:** The Telegram group becomes the **central coordination log** for agents + admin. Users enter ONLY via per-user secret code that identifies them in the DB.

**Rationale:**
- One channel for all agent-to-agent communication (Core, Code Operator, ChatGPT-Architect)
- All bots see the same commands — easier to orchestrate
- Per-user entry codes = secure invite + auto-identification
- Eliminates "who is this telegram_id?" lookups

**Dependencies (must fix BEFORE inviting users):**
1. Bot-to-bot filtering — bots must ignore each other's messages (currently spamming each other)
2. `entry_codes` table: `(code, user_id, used, expires_at)` — generates 1-time codes
3. Join-handler: when user joins group with code, validates + tags them
4. Default "closed" group state (admin-only to add)

**Status:** 🟡 ACCEPTED, dependencies pending

**Next:** after NIGHT_BRIEF economic fix is done, move to this.

---

### D-004 — Core Assistant overruns token budget (02:30)
**Context:** SLH Core Assistant sent 2 messages of ~3000 tokens each explaining role/token-efficiency. Irony: explaining efficiency is inefficient.

**Decision:** Code Operator (Claude Opus) does NOT acknowledge or engage with long theoretical messages. Only responds when concrete command is given (docker X, git Y, curl Z).

**Rationale:** User's budget is limited. Meta-discussion is free for Core (it's a separate AI), but I eat the context.

**Status:** ✅ ACTIVE policy

---

### D-003 — NIGHT_BRIEF = tonight's north star (02:20)
**Context:** Agents drifting between tasks (admin, bugs, bots, agents-plane).

**Decision:** `ops/NIGHT_BRIEF_20260417.md` = what we do tonight. Everything else is tomorrow.

**Goal:** 1+ new purchase + auto-approve endpoint for TON.

**Status:** ✅ ACTIVE

---

### D-002 — SILENT_MODE + rate-limit bug alerts (02:05)
**Context:** User drowning in Telegram notifications.

**Decision:** Added `SILENT_MODE=1` env var on API + rate-limit (max 1/5min, [AUTO] never alerts).

**Status:** ✅ DEPLOYED (commit a4758a0)

---

### D-001 — Stop 6 spammer bots locally (02:10)
**Context:** Bots spam in restart loops + multi-bot group membership.

**Decision:** Stopped: slh-core-bot, slh-admin, slh-ton-mnh, slh-campaign, slh-nifti, slh-nfty. Keep postgres/redis/device-registry/guardian/ledger running.

**Status:** ✅ ACTIVE. Revisit after root-cause fix (bot-to-bot filter).

---

## Template for new entries
```
### D-XXX — <short title> (HH:MM)
**Context:** <why this decision was needed>
**Decision:** <what was chosen>
**Rationale:** <why this beat alternatives>
**Status:** 🟢/🟡/🔴 <state>
**Next:** <what this enables>
```

---

## ⚠️ Don't re-debate
Agents (Core, Code Operator, ChatGPT-Architect): before proposing something, check if it's here. If it is and you want to change it — add a new D-entry saying why.

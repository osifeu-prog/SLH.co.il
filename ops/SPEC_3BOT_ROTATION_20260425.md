# SLH Spark · 3-Bot Token Rotation Spec · 2026-04-25
**Status:** SPEC — design only, not yet implemented.
**Purpose:** Multi-sig protocol over Telegram bots for rotating SLH secrets without single-bot compromise.
**Effort estimate:** 10-15 hours focused work + ongoing protocol maintenance.

---

## 🎯 Problem statement

Today, a single admin key (`slh_admin_2026_rotated_04_20`) can:
- Read all admin endpoints
- Send broadcasts to users
- Modify CRM data
- Trigger payments verification

If this key leaks (chat history, accidental commit, screenshare) — full system compromise.

**Goal:** rotation of any sensitive secret requires **2-of-3 separate Telegram bots to coordinate**, with each bot holding only a partial capability.

---

## 🏗 Architecture — 2-of-3 multisig

### The 3 bots

| Bot | Role | Can do | Cannot do |
|-----|------|--------|-----------|
| **🤖 KEY_PROPOSER** (`@SLH_KeyMaker_bot`) | Read + propose | List secrets (names only, NEVER values), generate new candidate values, create `proposal` record in DB | Activate. Approve. Read full secret values. |
| **🤖 KEY_AUDITOR** (`@SLH_KeyAudit_bot`) | Approve + log | Sign-approve proposals, view audit log, alert on suspicious patterns | Create proposals. Activate. |
| **🤖 KEY_ACTIVATOR** (`@SLH_KeyActivate_bot`) | Activate + propagate | Take an approved proposal and apply it (push to Railway env, update local services), send activated key to operator's DM ONCE | Create. Approve. Read prior keys. |

**Operator (Osif, tg=224223270) is whitelisted on all 3.** No other user can speak to any of them.

### Per-bot key holdings

Each bot has a **single Ed25519 keypair** generated at first run.
- Public keys are stored in `key_rotation_bots` table
- Private keys live in each bot's container (NOT shared, NOT committed)
- Bot signs every action with its private key

### Database schema

```sql
CREATE TABLE key_rotation_bots (
    bot_id          TEXT PRIMARY KEY,        -- 'proposer' | 'auditor' | 'activator'
    public_key      TEXT NOT NULL,           -- Ed25519 public key, base64
    last_seen       TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE key_rotation_proposals (
    id              SERIAL PRIMARY KEY,
    secret_name     TEXT NOT NULL,           -- 'ADMIN_API_KEYS' | 'JWT_SECRET' | etc.
    proposed_value_hash TEXT NOT NULL,       -- SHA-256 of new value (the value itself never in DB)
    proposed_value_encrypted BYTEA,           -- AES-256-GCM encrypted with operator pubkey
    status          TEXT NOT NULL DEFAULT 'proposed',  -- proposed | approved | activated | rejected | expired
    proposer_signature TEXT NOT NULL,
    approver_signature TEXT,
    activator_signature TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    approved_at     TIMESTAMP,
    activated_at    TIMESTAMP,
    expires_at      TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE TABLE key_rotation_audit (
    id              SERIAL PRIMARY KEY,
    proposal_id     INTEGER REFERENCES key_rotation_proposals(id),
    actor_bot_id    TEXT NOT NULL,
    action          TEXT NOT NULL,           -- propose | approve | reject | activate | expire
    payload_hash    TEXT,
    signature       TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 🔄 Rotation flow (operator's POV)

### Step 1 — Operator initiates from Telegram
```
Operator → @SLH_KeyMaker_bot: /rotate ADMIN_API_KEYS
```

### Step 2 — Proposer generates + records
```python
# Inside Proposer bot:
new_value = secrets.token_urlsafe(32)  # never logged
hash_ = hashlib.sha256(new_value.encode()).hexdigest()
encrypted = encrypt_for_operator(new_value, OPERATOR_PUBKEY)
sig = sign(payload, PROPOSER_PRIVATE_KEY)

# Insert into proposals table
proposal_id = db.insert(...)

# Reply to operator:
"📝 Proposal #42 created for ADMIN_API_KEYS
 Hash: a1b2c3...
 Forward this proposal to @SLH_KeyAudit_bot for review:
 /approve 42"
```

### Step 3 — Operator forwards to Auditor
```
Operator → @SLH_KeyAudit_bot: /approve 42
```

### Step 4 — Auditor signs approval
```python
# Auditor:
proposal = db.fetch(42)
verify_proposer_signature(proposal)
sig = sign(proposal_data, AUDITOR_PRIVATE_KEY)
db.update(42, status='approved', approver_signature=sig)

"✅ Proposal #42 approved.
 Send to @SLH_KeyActivate_bot to apply:
 /activate 42"
```

### Step 5 — Operator activates
```
Operator → @SLH_KeyActivate_bot: /activate 42
```

### Step 6 — Activator propagates
```python
# Activator:
proposal = db.fetch(42)
verify_proposer_signature(proposal)
verify_auditor_signature(proposal)
new_value = decrypt(proposal.encrypted_value, OPERATOR_PRIVATE_KEY)

# Push to Railway via API
railway_api.set_env(secret_name, new_value)

# Push to local docker via DB-published config (shared.config)
publish_config_to_bots(secret_name, new_value)

# Send to operator ONCE in encrypted DM
operator.send_message(f"🔐 ACTIVATED: ADMIN_API_KEYS = {new_value}")

# Audit
db.insert_audit(action='activate', signature=sign(...))
db.update(42, status='activated')
```

---

## 🛡 Security properties

| Property | Achieved by |
|----------|-------------|
| **No single point of compromise** | Need 2-of-3 bots to rotate; one rogue bot can't change anything |
| **No secret in DB plaintext** | All values stored encrypted with operator's pubkey |
| **Tamper detection** | Every action signed; chain verified before next step |
| **Replay protection** | Each proposal has unique ID + expiration |
| **Audit trail** | Immutable log table with signatures |
| **Operator-only access** | Each bot has telegram_id whitelist (224223270 only) |
| **Time-bound proposals** | 24h expiration auto-rejects stale proposals |

---

## ⚠️ Risks + mitigations

| Risk | Mitigation |
|------|-----------|
| **Bot private keys leak** | Generated in-container at first run; never committed; rotate the bot keys themselves periodically |
| **Operator's Telegram compromised** | All 3 bots verify via Telegram's own auth + hardware-key 2FA on operator's TG account (operator-side concern) |
| **Railway dashboard rotation bypasses bots** | Document in OPS_RUNBOOK that bots are PRIMARY rotation method; manual Railway changes log to audit table out-of-band |
| **One bot becomes unavailable** | 2-of-3 still works — any 2 bots can override any single failed bot. With 3-of-3 required for SOME secrets if needed. |
| **Operator forgets which secret needs rotation** | Periodic `/list_secrets` command on Proposer bot — names only, age-of-current-value, last-rotation-date |

---

## 📋 Implementation roadmap (phased)

### Phase 1 (3 hours) — Bare bones
- [ ] DB schema (3 tables) added to a new module `routes/key_rotation.py`
- [ ] 3 endpoints: `/api/keys/propose`, `/api/keys/approve`, `/api/keys/activate`
- [ ] Pydantic models for validation
- [ ] Audit logging on every action

### Phase 2 (4 hours) — Bot wrappers
- [ ] `key-proposer-bot` service in `docker-compose.yml`, copies of `bot_template.py` pattern
- [ ] `key-auditor-bot` service
- [ ] `key-activator-bot` service
- [ ] Each bot: 3-4 commands (list/propose/approve/activate based on role)
- [ ] Bot Ed25519 keypairs in container at first run, public keys registered in DB

### Phase 3 (3 hours) — Integration with Railway
- [ ] `_railway_set_env()` helper using Railway GraphQL API + service account token
- [ ] Local-side config refresh: when Activator updates, broadcasts via Redis pub/sub to all bot containers
- [ ] Railway service account token stored ONLY in Activator bot's env (single point — acceptable since Activator is the privileged role)

### Phase 4 (2 hours) — Operator UX
- [ ] Confirmation messages with clear next-step instructions
- [ ] Encryption of activated value in DM (so chat history doesn't leak)
- [ ] Status command: `/status` on any bot shows recent proposals + their state

### Phase 5 (3 hours) — Hardening
- [ ] Rate limiting (max 1 proposal/hour per secret)
- [ ] Anomaly detection in Auditor (flag proposals outside business hours)
- [ ] Backup of audit log to off-site (cloud storage)
- [ ] Drill: practice rotation in dev, time it end-to-end

**Total: 15 hours, can be split across 3 sessions of 5 hours each.**

---

## 🚦 When to build this

**NOT NOW.** Reasons:
1. Zero customers means zero financial blast radius from a key leak
2. Existing single-key system is "good enough" for current 21-user community
3. The 15 hours could go to acquiring customer #1 instead

**Build when:**
- You have 50+ paying customers (financial blast radius matters)
- Or you're considering institutional partners (their security review will require multi-sig)
- Or you've had a near-miss key leak that motivates the investment

**Until then:** rotate the existing single key manually every 30 days via Railway dashboard. Document each rotation in `ops/INCIDENTS.md` with timestamp.

---

## 🔗 Related docs

- `ops/SYSTEM_ARCHITECTURE.md` § 6 — Auth layers
- `ops/INCIDENTS.md` — past key-related incidents
- `routes/admin_rotate.py` — current single-key rotation endpoint (will be deprecated when this ships)
- `feedback_never_paste_secrets.md` — operator's standing rule on secrets in chat

---

_Last updated: 2026-04-25._
_Decision pending: build now, defer until customer-50, or build incrementally (Phase 1 only)._

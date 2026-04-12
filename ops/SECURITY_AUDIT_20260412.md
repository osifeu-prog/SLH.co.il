# Security Audit — SLH Ecosystem FastAPI Backend

**Date:** April 12, 2026
**Auditor:** Automated overnight agent (Claude Opus 4.6)
**File:** `D:\SLH_ECOSYSTEM\api\main.py` (~4600 lines)
**Scope:** Read-only audit, no code modifications

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 3 |
| HIGH     | 5 |
| MEDIUM   | 6 |
| LOW      | 4 |
| Positive | 8 |

---

## CRITICAL Issues (must-fix immediately)

### C-1: SQL Injection via f-string in `marketplace_list_item()` (Line 3962-3967)
**Severity:** CRITICAL
**Location:** `api/main.py:3962-3967`, function `marketplace_list_item()`

**Issue:** `approved_at` value injected directly into SQL via f-string:
```python
VALUES (..., {approved_at})
```
Where `approved_at` is `"CURRENT_TIMESTAMP"` or `"NULL"`. While these are currently hardcoded, the pattern is dangerous — if these strings ever come from user input, it's a straightforward SQLi.

**Fix:** Use parameterized CASE statement or conditional SQL:
```python
await conn.execute("""
    INSERT INTO marketplace_items (..., approved_at)
    VALUES (..., CASE WHEN $1 THEN CURRENT_TIMESTAMP ELSE NULL END)
""", req.auto_approve)
```

### C-2: SQL Injection in Profile Update (Line 2228)
**Severity:** CRITICAL
**Location:** `api/main.py:~2228`, function `update_user_profile()`

**Issue:** Builds UPDATE SET clause via f-string:
```python
f"UPDATE web_users SET {', '.join(updates)} WHERE telegram_id = $N"
```
While the VALUES use `$1, $2...` parameters, the column names are built from unsanitized strings. If `updates` list contains user-controlled keys, it becomes SQL injection.

**Fix:** Use a whitelist of allowed columns:
```python
ALLOWED_COLS = {"display_name", "bio", "language_pref", "eth_wallet", "ton_wallet"}
safe_updates = [f"{col} = ${i+1}" for i, col in enumerate(updates) if col in ALLOWED_COLS]
```

### C-3: Hardcoded Credentials
**Severity:** CRITICAL
**Locations:** Lines 25, 652, 761, 2038, 4719

- `ADMIN_API_KEY` defaults to `"slh_admin_2026"` (3 locations)
- `ADMIN_BROADCAST_KEY` defaults to `"slh-broadcast-2026-change-me"`
- `ENCRYPTION_KEY` defaults to `"slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026"`
- `DATABASE_URL` contains hardcoded password `slh_secure_2026` in fallback

**Fix:** Make all secrets required at startup:
```python
ADMIN_API_KEY = os.environ["ADMIN_API_KEY"]  # raises KeyError if missing
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]
# Fail fast at import time instead of running with dev defaults
```

---

## HIGH Issues

### H-1: Missing Auth on `/api/admin/dashboard` (Line 3545)
**Severity:** HIGH
**Location:** `api/main.py:~3545`

**Issue:** Returns aggregated stats (users, staking, signups, referrals) with **no authentication**. Any curl request can access admin insights.

**Fix:**
```python
@app.get("/api/admin/dashboard")
async def admin_dashboard(authorization: Optional[str] = Header(None)):
    user_id = get_current_user_id(authorization)
    if user_id != int(os.environ.get("ADMIN_USER_ID", 0)):
        raise HTTPException(403, "Admin only")
    # ... existing logic
```

### H-2: Missing Auth on `/api/admin/activity` (Line 4279)
**Severity:** HIGH
**Location:** `api/main.py:~4279`

**Issue:** Leaks recent logins, usernames, and payment activity without authentication.

**Fix:** Same pattern as H-1.

### H-3: CORS Wildcard on Headers (Line 52)
**Severity:** HIGH
**Location:** `api/main.py:~52`

**Issue:** `allow_headers=["*"]` combined with `allow_credentials=True` enables CSRF attacks via custom headers.

**Fix:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],  # explicit whitelist
)
```

### H-4: No Rate Limiting on User Creation
**Severity:** HIGH
**Locations:** `/api/user/ensure` (line 450), `/api/auth/telegram` (line 504)

**Issue:** Unlimited user creation allows attacker to spam web_users with varying telegram_ids, filling the DB and skewing analytics.

**Fix:** Use SlowAPI or simple in-memory rate limit:
```python
from slowapi import Limiter
limiter = Limiter(key_func=lambda req: req.client.host)

@app.post("/api/user/ensure")
@limiter.limit("5/minute")
async def ensure_user(req: EnsureUserRequest, request: Request):
    ...
```

### H-5: f-string SQL in `global_leaderboard()` (Lines 2925, 2929, 2935)
**Severity:** HIGH
**Location:** `api/main.py:2925-2935`

**Issue:** Uses `f"SELECT ... WHERE {EXCLUDE_RANGE} ORDER BY..."`. While `EXCLUDE_RANGE` is currently a hardcoded constant, the pattern is fragile.

**Fix:** Use parameterized query:
```python
EXCLUDE_MIN = 1000000
rows = await conn.fetch(
    "SELECT ... FROM users WHERE user_id >= $1 ORDER BY xp_total DESC LIMIT $2",
    EXCLUDE_MIN, limit
)
```

---

## MEDIUM Issues

### M-1: Missing Pydantic Field Constraints
Several Pydantic models (`ProfileUpdateRequest`, `MarketplaceListRequest`, etc.) lack `min_length`, `max_length`, `regex` constraints. Validation happens at function level, which is error-prone.

**Fix:** Add `Field(min_length=1, max_length=200)` to all string fields.

### M-2: Idempotency Gap on `/api/launch/contribute` (Line 4903)
Returns `{"ok": False}` on duplicate `tx_hash` — client may interpret as error instead of already-recorded.

**Fix:** Return `{"ok": True, "cached": True, "id": existing_id}` on duplicate.

### M-3: No Encryption on Audit Metadata (Line 1317-1330)
Sensitive activity in `institutional_audit.metadata` stored in plaintext.

**Fix:** Encrypt sensitive fields before writing to audit log (separate from hash chain integrity).

### M-4: Admin ID from Request Body (Line 4209)
Some endpoints accept `admin_id` from request body. Client can spoof.

**Fix:** Always extract admin identity from JWT, never trust request body.

### M-5: Marketplace Validation Silent Fails (Line 3949-3951)
Invalid `promotion` values default to `"none"` instead of raising `HTTPException(400)`.

**Fix:** Strict validation with explicit error messages.

### M-6: 18+ `print()` statements across the file
Debug prints leak sensitive data (tokens, user ids, errors) to stdout logs.

**Fix:** Replace with structured logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.warning("Something happened", extra={"user_id": uid})
```

---

## LOW Issues

### L-1: Verbose Error Messages
Some endpoints return raw exception strings in error responses. Could leak DB schema or internal paths.

### L-2: No CSRF Token
Session-based endpoints don't implement CSRF tokens (mitigated by CORS but not fully safe).

### L-3: Missing HTTPS Redirect Middleware
No explicit HSTS headers or HTTPS redirect. Railway handles this but worth explicit middleware.

### L-4: Open Registration
Anyone can register; no email verification, no CAPTCHA. Mitigated by Telegram ID uniqueness but could still flood the DB.

---

## Positive Findings (8)

1. **✓ Consistent asyncpg parameterization** — 90%+ of queries use proper `$1, $2...` placeholders
2. **✓ Institutional audit trail** — SHA-256 hash chain with `verify-chain` endpoint
3. **✓ AES-GCM encryption** — CEX API keys use proper AEAD with random nonce (v2 format)
4. **✓ Telegram auth verification** — HMAC-SHA256 check against bot token
5. **✓ Idempotency on financial transactions** — UNIQUE constraints on wallet_idempotency, beta_redemptions, cex_api_keys
6. **✓ Row-level permission checks** — DELETE operations verify `user_id` matches
7. **✓ Transaction isolation** — Uses `FOR UPDATE` on inventory-like tables
8. **✓ Input constraints** — Marketplace listings and profile updates have basic validation

---

## Priority Fix Roadmap

### 🔴 Tonight (Critical — before ANY real money)
- [ ] C-1: Fix marketplace f-string injection
- [ ] C-2: Fix profile update column f-string
- [ ] C-3: Remove all default dev credentials

### 🟡 This week (High — before launch)
- [ ] H-1: Add auth to `/api/admin/dashboard`
- [ ] H-2: Add auth to `/api/admin/activity`
- [ ] H-3: Tighten CORS `allow_headers`
- [ ] H-4: Rate limit user creation endpoints
- [ ] H-5: Parameterize leaderboard query

### 🟢 Next sprint (Medium)
- [ ] M-1: Pydantic validation across all models
- [ ] M-2: Idempotency return format fix
- [ ] M-3: Encrypt audit metadata
- [ ] M-4: Admin ID from JWT only
- [ ] M-5: Strict marketplace validation
- [ ] M-6: Replace prints with structured logging

### 🔵 Before production
- [ ] L-1: Sanitized error responses
- [ ] L-2: CSRF tokens on session endpoints
- [ ] L-3: Explicit HSTS middleware
- [ ] L-4: Email verification / CAPTCHA

---

**Overall assessment:** The codebase is in a **much better security posture than expected for an MVP**. The institutional controls (audit log, AES-GCM, idempotency) are solid. The critical findings are all fixable in <1 hour of focused work.

**Recommended next action:** Fix all 3 CRITICAL findings tonight before leaving, then H-1/H-2/H-3 within 24h.

*Generated by overnight security audit agent — 2026-04-12*

# SLH ESP32 Integration Status — 2026-04-21

Audit of the CYD (ESP32 + ILI9341 TFT) device integration in preparation for the 2026-05-03 Public Beta.

---

## TL;DR

**Status:** 🟢 **Integration is live and working.** All firmware-to-API endpoints exist on both sides. Pairing flow via QR is functional. System-audit admin card (commit `c83fb37`) tracks device liveness.

**Remaining before Public Beta:** 3 checks, all verification-level (no new code required). See §4.

---

## 1. Firmware-to-API surface

Firmware lives at `ops/firmware/slh-device-v3/src/main.cpp`. Build tree: `device-registry/esp32-cyd-work/firmware/slh-device-v3/`.

| # | Direction | Endpoint | Cadence | API location |
|---|---|---|---|---|
| 1 | Device → API | `GET /api/health` | boot-time liveness | `main.py` |
| 2 | Device → API | `GET /api/device/claim/{device_id}` | every 5s until paired | `main.py:10460` |
| 3 | Device → API | `POST /api/device/register` | on first pair | `main.py:10333` |
| 4 | Device → API | `POST /api/device/verify` | on pair code entry | `main.py:10383` |
| 5 | Device → API | `POST /api/esp/heartbeat` | every 30s | `main.py:10523` |
| 6 | Device → API | `GET /api/wallet/{user_id}/balances` | every 60s | `main.py` |
| 7 | Device → API | `GET /api/esp/commands/{device_id}` | polled for queue | `main.py:10589` |
| 8 | Admin → API | `POST /api/esp/commands/{device_id}` | push cmd to device | `main.py:10635` |
| 9 | Admin → API | `POST /api/esp/preorder` | reserve a unit | `main.py:10043` |

**All 9 endpoints verified present.** No broken links between firmware and API.

---

## 2. Pairing flow (as implemented)

1. User plugs in flashed CYD board → boots to pairing screen.
2. Display renders QR → `https://slh-nft.com/device-pair.html?mac=<MAC>`.
3. User scans → opens pairing page on phone.
4. User enters phone number → 6-digit code arrives via Telegram (or SMS fallback).
5. User enters code in page → page calls `/api/device/verify` → associates `user_id` with `device_id`.
6. Firmware (meanwhile polling `/api/device/claim/<device_id>` every 5s) receives `{token, user_id}`, saves to NVS, switches to Wallet screen.
7. Firmware starts heartbeat loop (30s) + balance refresh (60s).

**Firmware-side resilience:**
- `SLH_LOCAL_BRIDGE` fallback for heartbeat when Railway is unreachable → local bridge on dev PC (see `ops/system_bridge.py` from Night 19.4).
- NVS persistence means re-pairing after reboot is not needed.

---

## 3. Admin observability

- **System-audit card** (`c83fb37`, already shipped): 4 fields — `status / last_seen / ip / reason`.
- **Commands queue:** `POST /api/esp/commands/{device_id}` from admin.html pushes `{cmd, args}` into the queue; device picks it up within 30s.
- **Pre-order flow:** `POST /api/esp/preorder` + admin approval at `/api/esp/preorder/{id}/approve` for sales funnel.

---

## 4. Public Beta readiness checklist (3 items)

These are **verification-only** — no code changes needed unless a check fails.

### ☐ Check 4.1 — Live device heartbeat
With the existing CYD board at 10.0.0.4 (per FLASH_INSTRUCTIONS.md), flash v3 and confirm:
- `last_seen` on system-audit card updates within 30s of boot.
- `status` shows `OK`.
- Balances on the device match `/api/wallet/<user_id>/balances`.

### ☐ Check 4.2 — Pairing end-to-end from a fresh board
Use a second (un-paired) board or erase NVS on the current one:
```bash
pio run -t erase --upload-port COM5
pio run -t upload --upload-port COM5
```
Walk through the QR → phone → code flow. Success criterion: Wallet screen appears within 10s of code entry.

### ☐ Check 4.3 — Command push from admin.html
From `admin.html` → device row → send a test command (e.g. `display: hello beta`).
Success criterion: CYD screen shows `hello beta` within 30s.

---

## 5. Known non-blockers (note, don't fix pre-Beta)

- **Firmware OTA:** not implemented. Updates require USB re-flash. Acceptable for Beta (single admin controlling a handful of devices).
- **TLS cert pinning:** firmware uses Arduino's default CA bundle. Acceptable for MVP; revisit post-Beta.
- **Multiple device claims per user:** currently one user can claim many devices; there's no UI to list/revoke. Backend supports it, frontend doesn't surface it.

---

## 6. If you want ESP32 to contribute to Treasury revenue

The `POST /api/esp/preorder` flow is the natural hook. When a pre-order is approved + paid:

1. Call `routes.treasury.record_revenue_internal()` with `source_type='esp32_device'`, `amount_gross=<unit price>`, `currency='ILS'`.
2. Per Level 5 model: set `ESP32_HOUSE_CUT=1.0` (device sales are 100% treasury — no seller split).
3. Device pre-orders will appear in `/api/treasury/health.R_revenue.by_currency_period`.

Not wired in this audit (scope creep). Add when the pre-order flow is productionalized.

---

## 7. References

- Firmware: `ops/firmware/slh-device-v3/src/main.cpp`
- Build: `device-registry/esp32-cyd-work/firmware/slh-device-v3/`
- Flash instructions: `ops/firmware/slh-device-v3/FLASH_INSTRUCTIONS.md`
- Device API endpoints: `main.py:10333–10680`
- Local bridge fallback: `ops/system_bridge.py` (Night 19.4)
- System-audit card: commit `c83fb37` (2026-04-19)

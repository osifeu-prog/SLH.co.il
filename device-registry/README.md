# device-registry/

This folder used to host a toy 60-line in-memory FastAPI micro-service on port 8090.
**It was removed on 2026-04-20** because the real device-registry endpoints live on
the Railway API (authoritative, PostgreSQL-backed, Telegram code delivery, admin
commands, heartbeats audit).

## Canonical device-registry endpoints (Railway)

```
POST /api/device/register        — Step 1: phone + device_id → 6-digit code (TG or SMS)
POST /api/device/verify          — Step 2: validate code → issue signing_token
GET  /api/device/claim/{dev_id}  — Device polls after web pairing to pick up its token
POST /api/esp/heartbeat          — Device heartbeats (Bearer signing_token)
GET  /api/esp/commands/{dev_id}  — Device polls for admin commands
POST /api/esp/commands/{dev_id}  — Admin pushes commands (REBOOT, REVOKE, ...)
GET  /api/admin/devices/list     — Admin: list all devices
POST /api/admin/link-phone-tg    — Admin: link a phone to a Telegram id for code delivery
POST /api/esp/preorder           — Public: record an ESP preorder
POST /api/esp/preorder/{id}/approve — Admin: approve + auto-gift 2 SLH
```

See `ops/UNIFIED_CHAIN_DESIGN_20260420.md` for the full architecture.

## Remaining contents of this folder

- `esp32-cyd-work/` — the PlatformIO firmware workspace for the CYD device
  (board-specific includes, build flags, prior firmware variants). The latest
  v3 firmware source is tracked under `ops/firmware/slh-device-v3/` for git
  durability (the `firmware/` subdir here is gitignored due to its 148 MB of
  PlatformIO build output).

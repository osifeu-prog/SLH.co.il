# SLH Spark · Firmware Executor Agent Prompt · 2026-04-21
**Purpose:** Paste this entire prompt into a new Claude Code session to work on the ESP32 device firmware (OP-6). Focused scope — not the full ecosystem.
**Prerequisite:** ESP32 device physically connected via USB before starting.

---

## WHO I AM
- **Osif Kaufman Ungar** (@osifeu_prog, Telegram ID: 224223270)
- Windows 10 Pro, project root: `D:\SLH_ECOSYSTEM\`
- Hebrew UI, English code/commits, direct action style.

## SCOPE (this agent only)
- Location: `D:\SLH_ECOSYSTEM\ops\firmware\slh-device-v3\`
- Hardware target: ESP32 (family TBD — likely ESP32-WROOM or ESP32-S3, verify by reading `platformio.ini`)
- Build tool: PlatformIO (`pio` CLI)
- Deploy cmd: `pio run -t upload` (requires USB)
- Do NOT touch: API code (`api/main.py`), bots (`*-bot/`), website (`website/`). Firmware only.

## DEVICE ↔ API CONTRACT
The device talks to SLH Spark API at `https://slh-api-production.up.railway.app`.

Relevant endpoints (read-only reference — do NOT modify):
| Endpoint | Purpose |
|----------|---------|
| `POST /api/device/register` | Phone → 6-digit code (SMS or Telegram DM) |
| `POST /api/device/verify` | Code → device_id + secret (HMAC) |
| `POST /api/device/heartbeat` | Device pings every N sec (last_seen) |
| `GET /api/esp/commands/{device_id}` | Pull next queued command |
| `POST /api/esp/commands/{device_id}` | [admin-only] push command into queue |

Device auth: HMAC-SHA256 of request body with per-device secret from `/api/device/verify`.

## WHAT'S LIKELY IN THE FIRMWARE
(Verify by reading `slh-device-v3/` before assuming):
- `platformio.ini` — board, framework, libs
- `src/main.cpp` — setup + loop
- WiFi provisioning (SmartConfig or captive portal)
- HTTP/HTTPS client → SLH API
- OTA update support (maybe)
- Button/LED/sensor peripherals

## TASK KICKOFF CHECKLIST
When this session starts:
1. `cd D:\SLH_ECOSYSTEM\ops\firmware\slh-device-v3`
2. Read `platformio.ini` → confirm board + libs
3. `ls src/ include/ lib/` → map file structure
4. Ask Osif: "מה המטרה של הריצה הזו?" — flash existing build? Add feature? Fix bug? Debug serial output?
5. Confirm USB device is detected: `pio device list`
6. Only then start any code change.

## COMMANDS YOU'LL USE
```bash
pio run                      # build
pio run -t upload            # flash over USB
pio device monitor           # serial console (baud from platformio.ini)
pio device list              # list attached USB devices
pio check                    # static analysis
pio test                     # unit tests (if present)
```

## DO
- Read source before writing — firmware code is dense, misreading a pin definition bricks the device.
- Verify pins against the actual board schematic (ask Osif or read `hardware/` if present).
- Use `pio device monitor` after flash to confirm boot + WiFi + API handshake.
- Commit firmware changes separately from API/backend changes — different deploy path, different risk profile.

## DON'T
- Don't flash without confirming device is the right one (`pio device list` before every `upload`).
- Don't hardcode WiFi creds or API keys — use NVS (Preferences lib) or build-time `-D` flags from a gitignored file.
- Don't commit `.pio/build/` or `.pio/libdeps/` — these are build artifacts.
- Don't modify the API contract endpoints above without coordinating with the backend session.

## OPEN FIRMWARE ITEMS
| Item | Status | Notes |
|------|--------|-------|
| OP-6 firmware v3 flash | BLOCKED on hardware connection | Osif must USB-connect ESP32 before session starts |
| OTA update channel | unknown | Verify in source whether OTA is implemented |
| Heartbeat interval | unknown | Check `src/main.cpp` for `delay()` in main loop |

## HOW TO END A FIRMWARE SESSION
- Commit to `master` on `github.com/osifeu-prog/slh-api` (same repo as backend — firmware lives in `ops/firmware/`).
- Update `ops/firmware/slh-device-v3/CHANGELOG.md` with what flashed + device IDs that were reflashed.
- If OTA push is used, log the OTA URL + version bump in the handoff file for the next session.

# SLH Device v3 — Flash Instructions

## Prerequisites
- **Hardware:** CYD board (ESP32 + ILI9341 TFT). The one currently at 10.0.0.4 with `slh-v2` firmware.
- **Software:** PlatformIO (VS Code extension or CLI).
- **Cable:** USB-C data cable (data, not power-only).

## One-time setup
```powershell
# Install PlatformIO CLI if not present
pip install platformio
```

## Flash

```powershell
cd D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-v3

# Build
pio run

# Plug the CYD board via USB. Verify the COM port:
pio device list
# Note the COM port of "Silicon Labs CP210x" (or CH340) — e.g. COM5.

# Upload
pio run -t upload --upload-port COM5

# Watch serial (optional)
pio device monitor -p COM5 -b 115200
```

## Expected boot sequence (first flash after v2)

1. Display shows "SLH v3 Boot · Connecting WiFi..."
2. After ~3s: "WiFi OK: 10.0.0.x" (green)
3. Since NVS is empty → **Pairing screen** displays a QR code.
4. The QR contains: `https://slh-nft.com/device-pair.html?mac=<MAC>`.

## Pair the device

1. Scan the QR with your phone camera.
2. Open the resulting web page.
3. Enter your phone number — code arrives via Telegram (if phone is linked) or SMS.
4. Enter the 6-digit code in the page.
5. Page shows "✅ המכשיר קושר בהצלחה".
6. Within 5 seconds, the device polls `/api/device/claim/<device_id>`, picks up the token+user_id, saves to NVS, and switches to the Wallet screen.

## Expected Wallet screen

- Header: "SLH Wallet"
- User ID
- WiFi SSID + RSSI
- IP
- Device ID (first 12 chars of MAC)
- HB: OK / FAIL (every 30s — heartbeat to Railway)
- SLH: / MNH: / ZVK: balances (refreshed every 60s)

## Commands you can push from admin.html

Once paired, admins can push commands via `POST /api/esp/commands/{device_id}`:

- `REBOOT` — device restarts in ~1.5s
- `REVOKE` — wipes NVS + reboots (unpairs the device)
- _(future)_ `LED_RED`, `LED_GREEN`, `LED_BLUE`, `DISPLAY_TEXT:<msg>`

Example via curl:
```bash
curl -X POST "https://slh-api-production.up.railway.app/api/esp/commands/esp32-XXXXXXXXXXXX" \
  -H "X-Admin-Key: $SLH_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"REBOOT"}'
```

## Rollback to v2

If v3 misbehaves, keep the previous v2 binary around:

```powershell
cd D:\AISITE\esp32-heartbeat
# Re-flash with the v2 .ino via Arduino IDE
```

The two firmwares use the same hardware config — no need to reset NVS between switches.

## Factory reset (no serial)

Hold the BOOT button (GPIO0) for 3 seconds — the screen goes orange with "FACTORY RESET", NVS clears, device reboots to pairing mode.

## Env vars (build_flags) to tweak if needed

Edit `platformio.ini` `build_flags`:
- `SLH_API_HOST` — default `slh-api-production.up.railway.app`
- `SLH_LOCAL_BRIDGE` — default `http://10.0.0.7:5002` (your dev PC running `esp_bridge.py`)
- `SLH_PAIR_URL` — default `https://slh-nft.com/device-pair.html`

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Screen stays black | Wiring; `pio run -t clean && pio run` |
| WiFi FAILED loop | `WIFI_SSID` / `WIFI_PASS` in `src/main.cpp` top (Beynoni / 12345678) |
| QR won't scan | Re-open a scanner app at 20-30cm distance; lower TFT brightness |
| "HB: FAIL" | Railway reachable? `curl https://slh-api-production.up.railway.app/api/health` |
| Stuck on pair screen | Web pairing expired (>15min); scan QR again |
| Balance not updating | `pool.acquire` on Railway failed — check `/api/wallet/<uid>/balances` manually |

## Roadmap beyond v3

- v3.1: 5-way joystick + rotary encoder handling for on-device confirm
- v4: BLE pairing (skip web flow when phone can't scan)
- v4.1: Push notifications from Workers group (device rings when `guardian.alert` level=CRITICAL)

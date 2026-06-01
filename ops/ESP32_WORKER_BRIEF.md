# ESP32 CYD — Worker Brief (העובד השני)

**Assigned to:** [Worker Name]  
**Task:** Upload firmware to ESP32 device + full validation testing  
**Timeline:** 45 minutes  
**Device Port:** COM5 (already detected)  
**Expected Result:** Device boots, LED breathes blue, buttons respond, WiFi scans  

---

## 🎯 Mission

Upload working firmware to ESP32-CYD on COM5 and validate all systems work.

---

## ⚡ Step 1: Fix platformio.ini (2 minutes)

**File:** `D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device\platformio.ini`

**Replace entire content with:**

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino

monitor_speed = 115200
upload_speed = 115200
upload_protocol = esptool
upload_resetmethod = default

board_upload.flash_size = 4MB
board_upload.maximum_size = 1310720
```

**CRITICAL:** 
- Delete ALL `upload_flags` lines
- Delete ALL `--baud`, `--before`, `--after` parameters
- No extra boot parameters
- Save as UTF-8

---

## 🔨 Step 2: Build Firmware (3 minutes)

**PowerShell:**

```powershell
Set-Location "D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device"
pio run -t clean
pio run
```

**Expect to see:**
```
======================== [SUCCESS] Took X seconds ========================
RAM:   [=         ]  14.6% (used 47872 bytes from 327680 bytes)
Flash: [=======   ]  72.5% (used 950001 bytes from 1310720 bytes)
```

**If FAILS:**
- Stop. Report error to Osif immediately.
- Do NOT proceed to upload.

---

## 📤 Step 3: Upload Firmware (5 minutes)

**Command:**

```powershell
pio run -t upload --upload-port COM5
```

**Expect to see:**
```
Uploading .pio\build\esp32dev\firmware.bin
Connecting....
Chip is ESP32-D0WD-V3
Uploading stub...
Running stub...
Changing baud rate to 115200
Writing at [progress bar]...
Wrote 950256 bytes (950001 bytes compressed)
Hash of data verified
Leaving...
Hard resetting via RTS pin...
```

**If it fails with "chip stopped responding":**

1. Hold BOOT button (GPIO 0 - small button on board)
2. Run upload again:
   ```powershell
   pio run -t upload --upload-port COM5
   ```
3. Release BOOT when you see `Connecting...`

**If still fails:**

```powershell
pio run -t erase --upload-port COM5
pio run -t upload --upload-port COM5
```

**If STILL fails:**

```powershell
pio device list
mode COM5
```

Check COM5 exists. Close any other Serial monitors.

---

## 🧪 Step 4: Boot Validation (5 minutes)

**Open Serial Monitor:**

```powershell
pio device monitor -p COM5 -b 115200
```

**Look for boot messages:**
- ✅ System start
- ✅ Display init
- ✅ LED init (blue breathing)
- ✅ Button ready
- ✅ WiFi scan starting
- ❌ NO Guru Meditation errors
- ❌ NO Brownout resets
- ❌ NO Panic messages
- ❌ NO reboot loop

**Press Ctrl+C to exit monitor when done.**

---

## 📱 Step 5: Physical Device Tests (30 minutes)

### Display Check ✓
- Title should show: **"SLH DEVICE"** (cyan)
- Subtitle: **"WiFi Setup"** (white)
- Instructions visible
- NO white screen, NO artifacts

### LED Check ✓
- Should breathe **blue** in 10-second cycle
- NO flickering
- NO flashing
- Smooth breathing motion

### Button Tests ✓

**Test 1: Short Press (< 1 second)**
- LED should pulse blue once
- WiFi network list should scroll to next network
- Display should update with new highlight

**Test 2: Long Press (1-3 seconds)**
- Device should attempt WiFi connection
- Display shows "Connecting..."
- Serial monitor shows connection attempt

**Test 3: Very Long Press (3+ seconds)**
- LED should toggle on/off
- Display shows "LED ON" or "LED OFF"

### WiFi Test ✓

If you have a WiFi network available:
1. Press long button to connect to visible network
2. Device shows connecting message
3. Monitor serial for:
   - `[WiFi] Connecting to SSID...`
   - `[WiFi] Connected: 192.168.x.x`
4. IP address appears on display

---

## 📋 Report Back (EXACTLY this format)

```
UPLOAD RESULT:
- Success: YES / NO
- Last command: pio run -t upload --upload-port COM5
- Error (if failed): [exact text]

BOOT RESULT:
- Display OK: YES / NO
- LED breathing: YES / NO
- Serial clean: YES / NO

BUTTON TESTS:
- Short press: PASS / FAIL
- Long press: PASS / FAIL
- Very long press: PASS / FAIL

WIFI TEST:
- Scan OK: YES / NO
- Connect attempted: YES / NO
- Connected: YES / NO (if tested)
- IP received: [IP or N/A]

BLOCKERS:
[List any issues]

TIME TAKEN:
[Total minutes]

STATUS:
✅ READY FOR DEPLOYMENT / ⚠️ NEEDS FIXES / ❌ CRITICAL FAILURE
```

---

## 📞 If Blocked

**Issue:** Build fails  
**Action:** Stop. Report exact error to Osif.

**Issue:** Upload stuck at "Connecting..."  
**Action:** Try BOOT mode (hold button during upload).

**Issue:** Device boots but LED not breathing  
**Action:** Check serial logs. Report to Osif.

**Issue:** Button doesn't respond  
**Action:** Check GPIO 0 is soldered properly. Report to Osif.

**Issue:** WiFi can't connect  
**Action:** This is OK for now. Just confirm scan works.

---

## ✅ Success = Device Ready for API Integration

Once all tests pass, firmware is validated and ready for:
1. Device API endpoints creation
2. Device control dashboard
3. Real-time monitoring

**ETA: Ready by 18:00 (when you finish)**

Good luck! 🚀

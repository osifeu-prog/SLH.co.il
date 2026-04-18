# 🔧 ESP32-2432S028 GUIFION — Complete Fix Guide

---

## ✅ STEP 1: Check Device Detection

**בPowerShell, הרץ:**

```powershell
# רשימת כל ה-COM ports
Get-WmiObject Win32_SerialPort | Select-Object Name, Description, DeviceID
```

**מה אתה צריך לראות:**
```
Name        : COM5 (או COM3, COM4...)
Description : Silicon Labs CP2102 USB to UART Bridge Controller
             או
             CH340C USB UART
```

**אם זה לא מופיע:**
- 🔴 יש בעיית driver
- ↓ Skip to Step 2B (Driver Install)

**אם זה כן מופיע:**
- 🟢 Device מחובר בהצלחה
- ↓ Skip to Step 3 (Upload)

---

## ⚠️ STEP 2A: Check Device Manager

**Windows:**
1. פתח Device Manager: `devmgmt.msc`
2. חפש "Ports (COM & LPT)"
3. אתה צריך לראות:
   ```
   ✓ Silicon Labs CP2102 USB to UART Bridge (COMx)
   או
   ✓ CH340 Serial CH340 (COMx)
   ```

**אם אתה רואה "Unknown Device" או ⚠️:**
- 🔴 Driver חסר/כשל
- ↓ Go to Step 2B

**אם אתה רואה COMx:**
- 🟢 Driver בסדר
- ↓ Skip to Step 3

---

## 🔌 STEP 2B: Install USB Driver

**Option A: CP2102 Driver (Most Common)**

```powershell
# Download from Silicon Labs
$url = "https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip"
$output = "$env:DOWNLOADS\CP210x_driver.zip"
Invoke-WebRequest -Uri $url -OutFile $output

# Extract and install
Expand-Archive $output
# Follow Windows installation prompts
```

**Option B: CH340 Driver (If Option A doesn't work)**

```powershell
# Download from WinChipHead
$url = "http://www.wch.cn/downloads/CH341SER_EXE.html"
# Download manually from: http://www.wch.cn/downloads/CH341SER_EXE.html
# Extract CH341SER.EXE and run it
```

**After installing:**
1. Unplug ESP32
2. Restart computer
3. Plug ESP32 back in
4. Check Device Manager again

---

## 🔋 STEP 3: Check Power & Reset

**בדוק את ה-hardware:**

1. **Is device powered?**
   - Look for red LED on the ESP32 board
   - If no red LED → power issue
   
2. **Try manual reset:**
   - Unplug USB
   - Wait 5 seconds
   - Plug back in
   - You should see device appear in COM ports

3. **If still no power:**
   ```
   Possible issues:
   ❌ Bad USB cable (try different cable)
   ❌ USB port issue (try different USB port)
   ❌ Device firmware corrupted (see Step 6)
   ```

---

## 🚀 STEP 4: Download & Run Upload Script

**בPowerShell (Run as Administrator):**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

Then:

```powershell
cd "D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device"
.\UPLOAD_FIX.ps1
```

**Expected Output:**
```
Step 1: Clearing platformio cache...
✓ Cache cleared

Step 2: Clean rebuild...
[Building firmware...]
============= SUCCESS Took 30.5 seconds =============

Step 3: Waiting for device on COM5...
Make sure ESP32 is plugged into COM5

Step 4: Uploading with explicit 115200 baud...
Connecting...
Chip is ESP32-D0WD-V3
Uploading stub...
Running stub...
Changing baud rate to 115200
✓ Wrote firmware
✓ Hash verified

Step 5: Monitoring serial output...
[Device boots up...]
SLH DEVICE WIFI SELECTOR
```

---

## 🔴 STEP 5: If Upload Still Fails

**Error: "chip stopped responding"**

```
Solution:
1. Hold BOOT button (GPIO0) on ESP32
2. While holding BOOT, plug in USB
3. Release BOOT after 2 seconds
4. Try upload again
```

**Error: "espressif32 board not found"**

```powershell
pio boards | grep esp32
pio platform install espressif32
pio run -t upload --upload-port COM5
```

**Error: "COM5 not found"**

```powershell
# Check actual port
pio device list

# Replace COM5 with actual port (e.g., COM3)
pio run -t upload --upload-port COM3
```

---

## 📊 STEP 6: Firmware Verification (If Everything Else Fails)

**Erase and reformat device:**

```powershell
cd "D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device"

# Download esptool
pip install esptool

# Erase device
esptool.py --port COM5 erase_flash

# Then try upload again
pio run -t upload --upload-port COM5
```

---

## ✅ SUCCESS: What You Should See

**After successful upload:**

1. **Device boots:**
   ```
   ets Jul 29 2019 12:21:46
   rst:0x1 (POWERON_RESET)
   ...
   SLH DEVICE WIFI SELECTOR
   ```

2. **Display shows:**
   - Title: "SLH DEVICE" (cyan)
   - Subtitle: "WiFi Setup" (white)
   - Instructions (yellow/green)

3. **Backlight:**
   - Should be ON (bright)
   - Press button → WiFi list appears

4. **Serial monitor:**
   - Shows "SLH DEVICE WIFI SELECTOR"
   - No errors

---

## 🎯 QUICK TROUBLESHOOTING CHART

| Problem | Solution |
|---------|----------|
| No device in COM ports | Install CP2102/CH340 driver |
| "chip stopped responding" | Hold BOOT button during upload |
| "COM5 not found" | Check `pio device list` for actual port |
| No power (no red LED) | Try different USB cable/port |
| Device appears then disappears | Driver conflict, restart PC |
| Backlight not on | Run firmware with backlight fix |
| WiFi selector doesn't show | Firmware didn't upload, retry |

---

## 📞 Still Not Working?

**Provide these details:**

1. What error message do you see? (Copy exact text)
2. Output of: `pio device list`
3. Output of: `Get-WmiObject Win32_SerialPort | Select-Object Name, Description`
4. Device Manager screenshot (Ports section)
5. Which step is failing?

---

## 🚀 Once Device Is Online

**Test the connection:**

```powershell
# Monitor serial output
pio device monitor -p COM5 -b 115200
```

**You should see:**
```
SLH DEVICE WIFI SELECTOR
[waiting for button press]
```

**Try pressing button:**
- Short press → Next WiFi
- Long press (1+ sec) → Select & Connect

---

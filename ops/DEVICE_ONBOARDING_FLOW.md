# 📡 Device Onboarding Flow — Phone → Auto-Identify
> Unified flow: PC, ESP32, SIM-only devices, smart devices — all register with **just a phone number**.

## 🎯 המטרה
משתמש מזין **רק טלפון** → המערכת:
1. יוצרת/מוצאת `user_id` לפי הטלפון
2. מייצרת `device_id` ייחודי
3. מקשרת: `user_id ↔ device_id`
4. מתעדת את סוג המכשיר (PC / ESP / SIM / smartphone)
5. מחזירה signing token ל-API calls עתידיים

---

## 🧩 טבלאות נדרשות (2 חדשות)

```sql
-- Users identified by phone
CREATE TABLE IF NOT EXISTS users_by_phone (
    user_id BIGSERIAL PRIMARY KEY,
    phone TEXT UNIQUE NOT NULL,
    telegram_id BIGINT,        -- linked later if user adds TG
    display_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Devices linked to a user
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,           -- serial / MAC / UUID
    user_id BIGINT REFERENCES users_by_phone(user_id) ON DELETE SET NULL,
    device_type TEXT NOT NULL,            -- 'pc_windows', 'esp32', 'sim_gsm', 'smartphone'
    device_name TEXT,
    signing_token TEXT,                   -- used for authenticated API calls
    last_seen TIMESTAMP DEFAULT NOW(),
    registered_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_devices_user ON devices(user_id);
```

---

## 🔄 Endpoints (3 חדשים)

### 1. Register — תחילת תהליך
```
POST /api/device/register
Body: { phone: "0501234567", device_id: "ESP001", device_type: "esp32", device_name: "Gate sensor #1" }
Returns: { ok: true, verify_code: "124523", expires_in: 300 }
```
- שולח SMS או Telegram למספר עם קוד בן 6 ספרות
- אם אין TG לאותו מספר → SMS דרך ספק חיצוני (Twilio/Vonage)
- הקוד תקף 5 דקות

### 2. Verify — אישור קוד
```
POST /api/device/verify
Body: { phone: "0501234567", device_id: "ESP001", code: "124523" }
Returns: { ok: true, user_id: 42, signing_token: "<64-char>" }
```
- אם הקוד נכון → רושם ב-DB + מחזיר signing_token
- ESP32 שומר את הטוקן ב-Preferences (non-volatile)
- PC שומר ב-`~/.slh/device.json`

### 3. Sign — כל API call עתידי
```
POST /api/sign
Headers: { Authorization: "Bearer <signing_token>" }
Body: { action: "sensor_read", payload: {...} }
Returns: { ok: true, data: {...} }
```
- כל פעולה מאומתת אוטומטית מול ה-device_id
- אין צורך ב-phone/code יותר

---

## 🖥️ Per-device flow

### PC (Windows / Mac / Linux)
```powershell
# Osif: .\slh-register.ps1 -Phone "0501234567"
# Script:
$phone = Read-Host "Phone"
$deviceId = [Guid]::NewGuid().ToString()
$reg = Invoke-RestMethod -Uri "$API/api/device/register" -Method POST -Body (@{
    phone=$phone; device_id=$deviceId; device_type='pc_windows'; device_name=$env:COMPUTERNAME
} | ConvertTo-Json) -ContentType 'application/json'
Write-Host "Verify code sent. Paste here:"
$code = Read-Host
$verify = Invoke-RestMethod -Uri "$API/api/device/verify" -Method POST -Body (@{
    phone=$phone; device_id=$deviceId; code=$code
} | ConvertTo-Json) -ContentType 'application/json'
# Save token locally
@{ device_id=$deviceId; signing_token=$verify.signing_token } | ConvertTo-Json | Out-File "$env:USERPROFILE\.slh\device.json"
```

### ESP32 (Arduino / PlatformIO)
```cpp
// On first boot:
String phone = "0501234567";  // hardcoded or WiFi-provisioned
String devId = WiFi.macAddress();
// POST /api/device/register
// Display verify_code on OLED or wait for user to enter via button
// POST /api/device/verify → save signing_token to Preferences
preferences.putString("token", token);
// Subsequent boots: skip register, use saved token
```

### SIM-only ("dumb" device)
- **Assumption:** device can send SMS but has no IP
- **Flow:**
  1. Device sends SMS to `+972-5X-XXX-XXXX` (Twilio number)
  2. Body: `SLH REG ESP001 0501234567`
  3. Backend webhook receives → POST /api/device/register with device_type=`sim_gsm`
  4. Returns code via SMS to same phone
  5. Device replies: `SLH VERIFY 124523` → verified
  6. Future: device sends `SLH DATA <payload>` → backend signs automatically via stored token

### Smartphone (via Telegram bot)
```
User: /register 0501234567
Bot: 📱 שלחנו קוד ל-0501234567. הדבק אותו כאן.
User: 124523
Bot: ✅ מכשיר רשום! user_id=42. זה הדאשבורד שלך: https://slh-nft.com/dashboard.html?uid=42
```

---

## 🔐 Security notes
- **Signing token** = `hmac_sha256(device_id + user_id + SECRET)` — rotate quarterly
- **SMS cost:** ~$0.02/verify via Twilio. Cap at 3 attempts per phone/day.
- **One phone → many devices allowed** (same user can register many ESPs)
- **One device → one user** (device_id is PK)

---

## 🎯 Implementation order

### Phase 1 (can ship tomorrow)
- [ ] SQL migration 909_devices_users_by_phone.sql
- [ ] `/api/device/register` + `/api/device/verify` endpoints in main.py
- [ ] Telegram flow in core-bot (once stabilized)

### Phase 2 (week 1)
- [ ] Twilio webhook for SMS-based SIM devices
- [ ] PowerShell script `slh-register.ps1`
- [ ] Arduino sketch template `esp32-register-template.ino`

### Phase 3 (week 2)
- [ ] Unified dashboard `/admin-devices.html` — all devices, types, last seen
- [ ] Device heartbeat endpoint + auto-flag offline >1h

---

## 💡 Why this beats alternatives

| Alternative | Problem |
|-------------|---------|
| QR code per device | Doesn't work for SIM-only |
| Hardcode tokens in devices | Leaks if device stolen, can't revoke |
| OAuth via Google | Requires smartphone + account, excludes elderly/SIM users |
| SSH keys | Users can't generate them |
| **Phone + SMS code** | ✅ Universal, works for PC/ESP/SIM/smartphone |

---

**Spec ready for implementation. Estimated 4 hours for Phase 1.**

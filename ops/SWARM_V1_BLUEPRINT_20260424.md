# SLH Swarm v1 — Blueprint טכני + Roadmap
**תאריך:** 2026-04-24
**מחבר:** Osif (תכנון מקורי) + Claude Opus 4.7 (תיעוד/מיפוי ל-SLH stack)
**סטטוס:** Internal blueprint — NOT PRODUCTION, POC missing hardware

---

## 1. חזון

רשת פיזית מבוזרת של מכשירי ESP32 (nodes) שמתקשרים עם:
1. **אחד עם השני** (mesh local — ESP-NOW)
2. **טלפון אנדרואיד כ-Relay** (BLE/WiFi → Internet)
3. **Anchor Server** (SLH backend — ו-chain events)

**שימושים מיידיים ל-SLH:**
- **Kosher Wallet** — ESP32 + SMS במקום ארנק קריפטו אינטרנטי
- **Device Identity** — כל node חותם טרנזקציות ביד fizik
- **Proof-of-Presence** — hardware attestation לפגישות/אירועי SLH
- **DePIN-lite** — בסיס לכלכלה פיזית מבוזרת עם ZVK rewards לביזנס עסקים

---

## 2. ארכיטקטורה — שלוש שכבות

### L1: Device Layer (ESP32 Swarm)
- ESP32 boards (ESP32-S3 recommended, WROOM-32 compatible)
- תקשורת: **ESP-NOW** (primary, 2.4GHz, 250m line-of-sight) + **WiFi STA** (fallback)
- תפקידים:
  - חיישנים / אקטואטורים (דוגמה: כפתור sign transaction)
  - יצירת events מקומיים
  - חתימה קריפטוגרפית (ECDSA via mbedTLS)
  - local cache (~100KB SPIFFS/LittleFS)

### L2: Relay Layer (Phone)
- אנדרואיד = micro-server
- תקשורת: **BLE GATT** + **WiFi AP** עם ה-ESP, **HTTPS/WSS** החוצה
- תפקידים:
  - Gateway לאינטרנט
  - Message relay + buffer (SQLite local)
  - Telegram bot משלב UI
  - Node.js via Termux (POC) או app native (later)

### L3: Anchor Layer (SLH API)
- **אותו FastAPI על Railway** — לא שרת נפרד!
- תפקידים:
  - סנכרון גלובלי של events
  - rotate device keys
  - audit trail (hash chain הקיים)
  - חיבור ל-Ethereum/BSC עבור on-chain events
  - broadcast commands חזרה ל-devices

---

## 3. Protocol — SLH-MESH v1

### Format אחיד (JSON)
```json
{
  "id": "uuid-v4",
  "type": "event | command | state | heartbeat",
  "source": "device_id_hex",
  "target": "broadcast | device_id | anchor",
  "timestamp": 1710000000,
  "payload": { },
  "signature": "hex_ecdsa_signature"
}
```

### Message Types
| Type | Direction | Purpose |
|---|---|---|
| `event` | Device → Anchor | חיישן זיהה משהו, user לחץ |
| `command` | Anchor → Device | פעולה נדרשת (למשל sign tx) |
| `state` | Device → Anchor | מצב בריאות, battery, uptime |
| `heartbeat` | 2-way | keep-alive, כל 60s |

### Keys
- **Per-device private key** — נוצר בבוט ונשמר ב-NVS encrypted
- **Public key registered** ב-Anchor (table: `swarm_devices`)
- **Rotation** — אחת לחודש, או idempotent after user request

---

## 4. Kosher Wallet — First Real Use Case

### User Flow
1. משתמש חרדי רוכש את ה-device (₪888 pre-sale — כבר ב-roadmap.html)
2. Pair עם bot טלגרם (כפתור פיזי לחיצה כפולה → OTP SMS)
3. משתמש פותח flow "שלח SLH":
   - Bot שולח transaction draft ל-device דרך Phone relay
   - Device מציג בסיכום קצר: "שלח 10 SLH לאוסיף? כן/לא"
   - כפתור פיזי → signing
   - חתימה חוזרת ב-relay → Anchor → BSC
4. התשובה חוזרת ל-bot: "נשלח! hash=0x..."

### Why better than software wallet?
- **ללא אינטרנט על הטלפון של המשתמש** — ESP32 הוא המוצפן היחיד
- **כפתור פיזי = confirmation** — אי אפשר phishing דרך URL
- **SMS ≠ Internet** — מתאים לטלפון כשר 100%

---

## 5. POC Code Stub — ESP32 Side

```cpp
#include <WiFi.h>
#include <esp_now.h>
#include "mbedtls/ecdsa.h"
#include "mbedtls/sha256.h"

typedef struct __attribute__((packed)) {
  uint8_t type;          // 1=event, 2=cmd, 3=state, 4=heartbeat
  uint64_t timestamp;
  char payload[192];
  uint8_t signature[64]; // ECDSA
} SwarmMessage;

SwarmMessage msg;
uint8_t anchor_mac[] = {0x24,0x6F,0x28,0xAA,0xBB,0xCC}; // Phone relay MAC

void onSent(const uint8_t *mac, esp_now_send_status_t status) {
  Serial.printf("[SWARM] %s\n", status == ESP_NOW_SEND_SUCCESS ? "OK" : "FAIL");
}

void sign_message(SwarmMessage* m) {
  // TODO: mbedtls_ecdsa_write_signature over sha256(m->payload)
  // Private key loaded from NVS (encrypted partition)
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    Serial.println("[SWARM] ESP-NOW init failed");
    return;
  }

  esp_now_register_send_cb(onSent);

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, anchor_mac, 6);
  peer.channel = 0;
  peer.encrypt = false;
  esp_now_add_peer(&peer);
}

void loop() {
  msg.type = 1; // event
  msg.timestamp = (uint64_t)time(NULL);
  snprintf(msg.payload, sizeof(msg.payload), "{\"sensor\":\"button\",\"value\":1}");
  sign_message(&msg);

  esp_now_send(NULL, (uint8_t*)&msg, sizeof(msg));
  delay(60000);
}
```

## 6. POC Code Stub — Anchor (FastAPI) Side

Endpoint חדש שצריך להוסיף ל-`D:\SLH_ECOSYSTEM\api\main.py`:

```python
# routes/swarm.py (new file)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import hmac
from datetime import datetime

router = APIRouter(prefix="/api/swarm", tags=["swarm"])

class SwarmMessage(BaseModel):
    id: str
    type: str
    source: str
    target: str
    timestamp: int
    payload: dict
    signature: str

@router.post("/ingest")
async def ingest_swarm_event(msg: SwarmMessage):
    # 1. Verify signature against registered public key
    from sqlalchemy import text
    from main import async_session  # reuse existing pool

    async with async_session() as s:
        r = await s.execute(
            text("SELECT public_key_hex FROM swarm_devices WHERE device_id = :d"),
            {"d": msg.source}
        )
        row = r.first()
        if not row:
            raise HTTPException(403, "device not registered")

        # TODO: actual ECDSA verify with row.public_key_hex

        # 2. Store event (reuses hash chain from events table)
        await s.execute(
            text("""
                INSERT INTO swarm_events
                (event_id, device_id, event_type, payload, created_at)
                VALUES (:id, :src, :typ, :pl, NOW())
            """),
            {"id": msg.id, "src": msg.source, "typ": msg.type, "pl": str(msg.payload)}
        )
        await s.commit()

    return {"ok": True, "received_at": datetime.utcnow().isoformat()}


@router.get("/devices/{device_id}/pending")
async def get_pending_commands(device_id: str):
    # Device polls for commands addressed to it
    async with async_session() as s:
        r = await s.execute(
            text("""
                SELECT command_id, command_type, payload
                FROM swarm_commands
                WHERE target_device = :d AND delivered_at IS NULL
                ORDER BY created_at ASC LIMIT 10
            """),
            {"d": device_id}
        )
        return {"commands": [dict(row._mapping) for row in r.fetchall()]}
```

### DB Schema (2 tables)
```sql
CREATE TABLE swarm_devices (
  device_id TEXT PRIMARY KEY,       -- hex MAC or uuid
  owner_user_id INT REFERENCES users(id),
  public_key_hex TEXT NOT NULL,
  device_type TEXT,                  -- 'wallet', 'sensor', 'beacon'
  registered_at TIMESTAMPTZ DEFAULT NOW(),
  last_heartbeat TIMESTAMPTZ,
  status TEXT DEFAULT 'active',      -- 'active','revoked','lost'
  metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE swarm_events (
  id SERIAL PRIMARY KEY,
  event_id UUID UNIQUE,
  device_id TEXT REFERENCES swarm_devices(device_id),
  event_type TEXT,
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  INDEX idx_swarm_events_device (device_id, created_at DESC)
);

CREATE TABLE swarm_commands (
  id SERIAL PRIMARY KEY,
  command_id UUID UNIQUE,
  target_device TEXT REFERENCES swarm_devices(device_id),
  command_type TEXT,
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  delivered_at TIMESTAMPTZ,
  ack_at TIMESTAMPTZ
);
```

---

## 7. Phone Relay (Termux POC)

```javascript
// relay.js — run via `node relay.js` on Termux (Android)
const WebSocket = require('ws');
const noble = require('@abandonware/noble'); // BLE

const ANCHOR_WS = 'wss://slh-api-production.up.railway.app/ws/swarm';
const DEVICE_UUID = '0000ffe0-0000-1000-8000-00805f9b34fb'; // SLH Swarm BLE UUID

let anchor = new WebSocket(ANCHOR_WS);

anchor.on('open', () => console.log('[Relay] Connected to Anchor'));
anchor.on('message', (data) => {
  // Forward commands from Anchor → ESP via BLE
  console.log('[Anchor→Device]', data.toString());
  // TODO: noble.writeCharacteristic(...)
});

noble.on('discover', (peripheral) => {
  if (peripheral.advertisement.localName?.startsWith('SLH-')) {
    peripheral.connect(() => {
      peripheral.discoverServices([], (err, services) => {
        // Subscribe to notifications, forward to Anchor
        console.log('[Relay] Device paired:', peripheral.uuid);
      });
    });
  }
});

noble.startScanning([DEVICE_UUID], true);
```

---

## 8. Integration with SLH Ecosystem

### Existing Systems שמשתלבים
| SLH Component | איך swarm משתלב |
|---|---|
| `swarm_events` table | ה-event נרשם כמו אירוע audit רגיל עם hash chain |
| ZVK token | device מקבל ZVK על Proof-of-Presence |
| Telegram bot `@SLH_AIR_bot` | bot מציג status של device המשתמש |
| Admin panel | `/admin.html` → tab חדש "Swarm" — list/rotate/revoke |
| Network map (`/network.html`) | device nodes מופיעים כסוג חדש `swarm` |

### Endpoints חדשים שצריך ל-`main.py`
```
POST   /api/swarm/register      — Admin adds device_id + public_key
POST   /api/swarm/ingest        — Device POSTs event (signed)
GET    /api/swarm/devices       — List all (admin)
GET    /api/swarm/devices/:id   — Device detail + history
POST   /api/swarm/commands      — Admin sends command to device
GET    /api/swarm/devices/:id/pending — Device polls commands
POST   /api/swarm/heartbeat     — Device pings alive
```

---

## 9. Roadmap — זמן בנייה משוער

### Phase 0: Pre-work (היום — 2026-04-24)
- [x] Blueprint (המסמך הזה)
- [ ] הזמנת 2-3 יחידות ESP32 (₪150 סה"כ) — Osif action
- [ ] OTA firmware signing key generation — dev action

### Phase 1: POC (2-3 שבועות)
- [ ] Firmware basic: ESP-NOW send + receive, LED blink on receive
- [ ] DB schema: 3 טבלאות
- [ ] 7 endpoints ב-`api/swarm.py`
- [ ] Termux relay script (Node.js)
- [ ] 1 device פועל end-to-end עם Anchor
- **Success criterion:** event מ-ESP מופיע ב-`swarm_events` ב-Postgres

### Phase 2: Multi-device + Wallet (4-6 שבועות)
- [ ] 3 devices משודרים בו-זמנית
- [ ] mesh hop אמיתי (device A → B → Phone → Anchor)
- [ ] ECDSA signing מיושם מלא
- [ ] Kosher Wallet POC: sign SLH transaction דרך כפתור פיזי
- [ ] Admin UI `/admin.html#swarm`

### Phase 3: Production Hardware (3-6 חודשים)
- [ ] PCB design (ESP32-S3 + secure element ATECC608A)
- [ ] Enclosure
- [ ] Manufacturing run של 100 יחידות (₪888 pre-sale ב-roadmap.html — כבר קיים!)
- [ ] App Android native (לא Termux)
- [ ] השקה מסחרית

### Phase 4: DePIN Economy (2027+)
- [ ] Geographic mapping (proof-of-location)
- [ ] ZVK rewards עבור heartbeat/events
- [ ] Integration with marketplace (device scanning → pay)
- [ ] Multi-hop mesh networks בקהילות חרדיות ללא wifi

---

## 10. מה DONT לעשות

- ❌ אל תבנה custom PCB ב-Phase 1 — השתמש ב-dev boards (₪50/חתיכה)
- ❌ אל תטעין crypto keys production לפני אבטחה רצינית (HSM / secure element)
- ❌ אל תפרסם "Swarm Network LIVE" באתר לפני Phase 2
- ❌ אל תשלח OTA updates ללא firmware signing
- ❌ אל תחשוף endpoints `/api/swarm/*` לפני rate limiting + auth

---

## 11. Decision Points

### לפני Phase 1
- [ ] **Osif:** האם להזמין 3 יחידות ESP32 השבוע? (₪150)
- [ ] **Osif:** Termux installed on phone? (free)
- [ ] **Osif:** Budget ל-$10/חודש TLS certificate (אם לא Railway)?

### לפני Phase 2
- [ ] האם Kosher Wallet ב-₪888 יממן את הפיתוח? (רכישה מוקדמת 100 = ₪88,800 = מימון Phase 2+3)
- [ ] האם נצטרך יועמ"ש לתקנות ארנק חומרה?

### לפני Phase 3
- [ ] רגולציה: קריפטו + hardware wallet + חרדים = שלישיית סיכון — בדיקה מקדימה
- [ ] ייצור: סין (זול, איטי) או ישראל (יקר, גמיש)?

---

## 12. Dependencies / Blockers

| Blocker | Owner | Status |
|---|---|---|
| רכישת ESP32 dev boards | Osif | ❌ לא הוזמן |
| Termux על הטלפון | Osif | ? |
| מקום להניח device בבית | Osif | ✅ יש |
| Firmware signing key | dev | ❌ טרם נוצר |
| `api/swarm.py` file | dev | ❌ טרם נכתב |
| `/swarm.html` vision page | dev | ✅ נבנה הלילה |

---

**End of document — 2026-04-24**
**Next action:** Build `/swarm.html` + `/voice.html` + update network.html + project-map.html + roadmap.html

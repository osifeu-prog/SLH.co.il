// SLH Device Firmware v3 — Railway-integrated kosher wallet
// Build: PlatformIO (esp32dev board) — see platformio.ini
// Hardware: CYD (Cheap Yellow Display) — ESP32 + ILI9341 TFT 240x320 + button on GPIO0

#include <Arduino.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <qrcode.h>

#define BTN_PIN 0
#define HEARTBEAT_INTERVAL_MS 30000UL
#define BALANCE_INTERVAL_MS   60000UL
#define COMMAND_POLL_MS       15000UL
#define WIFI_SSID "Beynoni"
#define WIFI_PASS "12345678"

TFT_eSPI tft = TFT_eSPI();
Preferences prefs;

String gDeviceId = "";      // persisted MAC-based
String gSigningToken = "";  // from /api/device/verify
int64_t gUserId = 0;        // from /api/device/verify

unsigned long lastHeartbeatMs = 0;
unsigned long lastBalanceMs = 0;
unsigned long lastCommandPollMs = 0;

// ---- utility ----
String macClean() {
  String m = WiFi.macAddress();
  m.replace(":", "");
  return m;
}

void drawHeader(const String& title) {
  tft.fillRect(0, 0, 240, 30, TFT_NAVY);
  tft.setTextColor(TFT_WHITE, TFT_NAVY);
  tft.setTextSize(2);
  tft.setCursor(4, 6);
  tft.print(title);
}

void drawStatusLine(int y, const String& text, uint16_t color = TFT_LIGHTGREY) {
  tft.fillRect(0, y, 240, 20, TFT_BLACK);
  tft.setTextColor(color, TFT_BLACK);
  tft.setTextSize(1);
  tft.setCursor(4, y + 4);
  tft.print(text);
}

// ---- QR pairing screen ----
void showPairingScreen() {
  tft.fillScreen(TFT_BLACK);
  drawHeader("SLH Pair Me");

  String url = String(SLH_PAIR_URL) + "?mac=" + macClean();
  QRCode qr;
  uint8_t qrData[qrcode_getBufferSize(4)];
  qrcode_initText(&qr, qrData, 4, 0, url.c_str());

  int boxSize = 4;
  int offsetX = (240 - qr.size * boxSize) / 2;
  int offsetY = 40;
  tft.fillRect(offsetX - 4, offsetY - 4,
               qr.size * boxSize + 8, qr.size * boxSize + 8, TFT_WHITE);
  for (int y = 0; y < qr.size; y++) {
    for (int x = 0; x < qr.size; x++) {
      if (qrcode_getModule(&qr, x, y)) {
        tft.fillRect(offsetX + x * boxSize, offsetY + y * boxSize,
                     boxSize, boxSize, TFT_BLACK);
      }
    }
  }
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.setCursor(4, offsetY + qr.size * boxSize + 8);
  tft.print("Scan to pair:");
  tft.setCursor(4, offsetY + qr.size * boxSize + 20);
  tft.print(url);
  tft.setCursor(4, 300);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.print("MAC: ");
  tft.print(macClean());
}

void showBalanceScreen() {
  tft.fillScreen(TFT_BLACK);
  drawHeader("SLH Wallet");
  drawStatusLine(32, "User: " + String((long)gUserId), TFT_GREEN);
  drawStatusLine(48, "WiFi: " + WiFi.SSID() + "  " + String(WiFi.RSSI()) + "dBm", TFT_LIGHTGREY);
  drawStatusLine(64, "IP: " + WiFi.localIP().toString(), TFT_LIGHTGREY);
  drawStatusLine(80, String("Device: ") + gDeviceId.substring(0, 12), TFT_LIGHTGREY);
}

// ---- NVS persistence ----
void loadPrefs() {
  prefs.begin("slh", true);
  gDeviceId = prefs.getString("device_id", "");
  gSigningToken = prefs.getString("token", "");
  gUserId = prefs.getLong64("user_id", 0);
  prefs.end();

  if (gDeviceId.length() == 0) {
    gDeviceId = "esp32-" + macClean();
  }
}

void savePrefs() {
  prefs.begin("slh", false);
  prefs.putString("device_id", gDeviceId);
  prefs.putString("token", gSigningToken);
  prefs.putLong64("user_id", gUserId);
  prefs.end();
}

void clearPrefs() {
  prefs.begin("slh", false);
  prefs.clear();
  prefs.end();
  gSigningToken = "";
  gUserId = 0;
}

// ---- WiFi ----
bool wifiConnect() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(200);
  }
  return WiFi.status() == WL_CONNECTED;
}

// ---- API helpers ----
bool railwayReachable() {
  HTTPClient http;
  String url = String("https://") + SLH_API_HOST + "/api/health";
  http.begin(url);
  http.setTimeout(4000);
  int code = http.GET();
  http.end();
  return code == 200;
}

bool postHeartbeat() {
  if (gSigningToken.length() == 0) return false;

  StaticJsonDocument<512> doc;
  doc["device_id"] = gDeviceId;
  doc["fw"] = SLH_FW_TAG;
  doc["ssid"] = WiFi.SSID();
  doc["rssi"] = WiFi.RSSI();
  doc["ip"] = WiFi.localIP().toString();
  doc["uptime_seconds"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  String payload;
  serializeJson(doc, payload);

  // Primary: Railway
  {
    HTTPClient http;
    String url = String("https://") + SLH_API_HOST + "/api/esp/heartbeat";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + gSigningToken);
    http.setTimeout(6000);
    int code = http.POST(payload);
    http.end();
    if (code >= 200 && code < 300) return true;
    Serial.printf("[hb] railway ret %d, trying local fallback\n", code);
  }

  // Fallback: local bridge (best-effort, no auth)
  {
    HTTPClient http;
    String url = String(SLH_LOCAL_BRIDGE) + "/api/esp/heartbeat";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(4000);
    int code = http.POST(payload);
    http.end();
    return (code >= 200 && code < 300);
  }
}

bool fetchBalances(String& tokenLine1, String& tokenLine2, String& tokenLine3) {
  if (gUserId == 0 || gSigningToken.length() == 0) return false;
  HTTPClient http;
  String url = String("https://") + SLH_API_HOST + "/api/wallet/" + String((long)gUserId) + "/balances";
  http.begin(url);
  http.addHeader("Authorization", String("Bearer ") + gSigningToken);
  http.setTimeout(6000);
  int code = http.GET();
  if (code < 200 || code >= 300) {
    http.end();
    return false;
  }
  String body = http.getString();
  http.end();

  StaticJsonDocument<2048> doc;
  DeserializationError err = deserializeJson(doc, body);
  if (err) return false;

  // Extract top 3 tokens (SLH, MNH, ZVK) if present
  auto balances = doc["balances"].as<JsonObject>();
  tokenLine1 = String("SLH: ") + String((double)balances["SLH"] | 0.0, 4);
  tokenLine2 = String("MNH: ") + String((double)balances["MNH"] | 0.0, 2);
  tokenLine3 = String("ZVK: ") + String((double)balances["ZVK"] | 0.0, 2);
  return true;
}

bool pollClaim() {
  HTTPClient http;
  String url = String("https://") + SLH_API_HOST + "/api/device/claim/" + gDeviceId;
  http.begin(url);
  http.setTimeout(6000);
  int code = http.GET();
  if (code != 200) { http.end(); return false; }
  String body = http.getString();
  http.end();

  StaticJsonDocument<512> doc;
  if (deserializeJson(doc, body)) return false;
  bool paired = doc["paired"] | false;
  if (!paired) return false;

  const char* tok = doc["signing_token"] | "";
  int64_t uid = doc["user_id"] | 0;
  if (strlen(tok) < 16 || uid == 0) return false;

  gSigningToken = String(tok);
  gUserId = uid;
  savePrefs();
  Serial.printf("[pair] claimed! user_id=%lld token_len=%d\n", (long long)uid, (int)gSigningToken.length());
  return true;
}

String pollCommand() {
  if (gSigningToken.length() == 0) return "";
  HTTPClient http;
  String url = String("https://") + SLH_API_HOST + "/api/esp/commands/" + gDeviceId;
  http.begin(url);
  http.addHeader("Authorization", String("Bearer ") + gSigningToken);
  http.setTimeout(4000);
  int code = http.GET();
  if (code != 200) {
    http.end();
    return "";
  }
  String body = http.getString();
  http.end();
  StaticJsonDocument<512> doc;
  if (deserializeJson(doc, body)) return "";
  const char* cmd = doc["command"] | "";
  return String(cmd);
}

void handleCommand(const String& cmd) {
  if (cmd.length() == 0) return;
  Serial.printf("[cmd] received: %s\n", cmd.c_str());
  if (cmd == "REBOOT") {
    tft.fillScreen(TFT_RED);
    tft.setTextColor(TFT_WHITE, TFT_RED);
    tft.setTextSize(2);
    tft.setCursor(20, 140);
    tft.print("REBOOTING...");
    delay(1500);
    ESP.restart();
  } else if (cmd == "REVOKE") {
    clearPrefs();
    tft.fillScreen(TFT_ORANGE);
    tft.setTextColor(TFT_BLACK, TFT_ORANGE);
    tft.setTextSize(2);
    tft.setCursor(10, 140);
    tft.print("REVOKED");
    delay(2000);
    ESP.restart();
  }
  // PING, LED_*, DISPLAY_* can be added here
}

void setup() {
  Serial.begin(115200);
  delay(200);

  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_BLACK);

  pinMode(BTN_PIN, INPUT_PULLUP);

  loadPrefs();

  drawHeader("SLH v3 Boot");
  drawStatusLine(40, "Connecting WiFi...");
  if (!wifiConnect()) {
    drawStatusLine(60, "WiFi FAILED — retry in 30s", TFT_RED);
    delay(30000);
    ESP.restart();
  }
  drawStatusLine(60, "WiFi OK: " + WiFi.localIP().toString(), TFT_GREEN);

  if (gSigningToken.length() == 0) {
    delay(1200);
    showPairingScreen();
  } else {
    delay(500);
    showBalanceScreen();
  }
}

void loop() {
  unsigned long now = millis();

  // Long-press BTN (>3s) → factory reset
  static unsigned long pressStart = 0;
  int btn = digitalRead(BTN_PIN);
  if (btn == LOW) {
    if (pressStart == 0) pressStart = now;
    if (now - pressStart > 3000) {
      clearPrefs();
      tft.fillScreen(TFT_ORANGE);
      tft.setTextColor(TFT_BLACK, TFT_ORANGE);
      tft.setTextSize(2);
      tft.setCursor(10, 140);
      tft.print("FACTORY RESET");
      delay(2000);
      ESP.restart();
    }
  } else {
    pressStart = 0;
  }

  // Pairing: if unpaired, poll /api/device/claim every 5s
  if (gSigningToken.length() == 0) {
    static unsigned long lastPairPollMs = 0;
    if (now - lastPairPollMs > 5000) {
      lastPairPollMs = now;
      if (pollClaim()) {
        showBalanceScreen();
      }
    }
    delay(100);
    return;  // don't heartbeat/balance/command until paired
  }

  // Heartbeat
  if (now - lastHeartbeatMs > HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatMs = now;
    bool ok = postHeartbeat();
    drawStatusLine(100, String("HB: ") + (ok ? "OK" : "FAIL"), ok ? TFT_GREEN : TFT_ORANGE);
  }

  // Balance refresh (only if paired)
  if (gSigningToken.length() > 0 && now - lastBalanceMs > BALANCE_INTERVAL_MS) {
    lastBalanceMs = now;
    String l1, l2, l3;
    if (fetchBalances(l1, l2, l3)) {
      drawStatusLine(140, l1, TFT_CYAN);
      drawStatusLine(160, l2, TFT_CYAN);
      drawStatusLine(180, l3, TFT_CYAN);
    } else {
      drawStatusLine(140, "Balance fetch failed", TFT_ORANGE);
    }
  }

  // Command poll
  if (gSigningToken.length() > 0 && now - lastCommandPollMs > COMMAND_POLL_MS) {
    lastCommandPollMs = now;
    String cmd = pollCommand();
    if (cmd.length() > 0) handleCommand(cmd);
  }

  delay(100);
}

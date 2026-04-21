// SLH Device v3 — Railway-integrated hardware wallet
// ILI9341 TFT (landscape 320x240), ESP32, WiFiManager, NVS, QR pairing

#include <Arduino.h>
#include <Preferences.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>
#include <qrcode.h>

// ─── Build-time config (from platformio.ini build_flags) ──────
#ifndef SLH_API_HOST
  #define SLH_API_HOST "slh-api-production.up.railway.app"
#endif
#ifndef SLH_PAIR_URL
  #define SLH_PAIR_URL "https://slh-nft.com/device-pair.html"
#endif
#ifndef SLH_FW_TAG
  #define SLH_FW_TAG "slh-v3"
#endif
#ifndef TFT_BL
  #define TFT_BL 21
#endif

#define API_BASE              "https://" SLH_API_HOST
#define CLAIM_INTERVAL_MS     3000UL
#define HEARTBEAT_INTERVAL_MS 60000UL
#define BALANCE_INTERVAL_MS   60000UL

// ─── Globals ──────────────────────────────────────────────────
TFT_eSPI   tft   = TFT_eSPI();
Preferences prefs;

String  g_device_id;
String  g_signing_token;
int     g_user_id = 0;
uint32_t g_last_heartbeat = 0;
uint32_t g_last_balance   = 0;
uint32_t g_last_claim     = 0;

enum State { BOOTING, PAIRING, PAIRED };
State g_state = BOOTING;

// ─── Colors ───────────────────────────────────────────────────
#define C_BG    TFT_BLACK
#define C_GOLD  0xFEA0
#define C_GRAY  0x8410

// ─── Device ID / MAC ──────────────────────────────────────────
String makeDeviceId() {
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  char buf[32];
  snprintf(buf, sizeof(buf), "slh-%02x%02x%02x%02x%02x%02x",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return buf;
}

String getMacStr() {
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  char buf[20];
  snprintf(buf, sizeof(buf), "%02x%02x%02x%02x%02x%02x",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return buf;
}

// ─── NVS ──────────────────────────────────────────────────────
void loadPrefs() {
  prefs.begin("slh", true);
  g_signing_token = prefs.getString("token", "");
  g_user_id       = prefs.getInt("uid", 0);
  prefs.end();
}

void saveToken(const String& token, int uid) {
  prefs.begin("slh", false);
  prefs.putString("token", token);
  prefs.putInt("uid", uid);
  prefs.end();
}

// ─── Draw helpers (landscape 320×240) ────────────────────────
void drawHeader(const char* title) {
  tft.fillRect(0, 0, 320, 28, C_GOLD);
  tft.setTextColor(TFT_BLACK, C_GOLD);
  tft.setTextSize(2);
  tft.setCursor(8, 6);
  tft.print(title);
}

void drawStatus(const char* msg, uint16_t color = C_GRAY) {
  tft.fillRect(0, 224, 320, 16, C_BG);
  tft.setTextColor(color, C_BG);
  tft.setTextSize(1);
  tft.setCursor(4, 228);
  tft.print(msg);
}

void drawBootScreen() {
  tft.fillScreen(C_BG);
  drawHeader("SLH Spark");
  tft.setTextColor(C_GOLD, C_BG);
  tft.setTextSize(3);
  tft.setCursor(100, 80);
  tft.print("SLH");
  tft.setTextColor(TFT_WHITE, C_BG);
  tft.setTextSize(1);
  tft.setCursor(85, 125);
  tft.print("Hardware Wallet " SLH_FW_TAG);
  drawStatus("Booting...", C_GRAY);
}

void drawWiFiSetupScreen() {
  tft.fillScreen(C_BG);
  drawHeader("WiFi Setup");
  tft.setTextColor(TFT_WHITE, C_BG);
  tft.setTextSize(1);
  tft.setCursor(10, 40);  tft.print("Connect to WiFi network:");
  tft.setTextColor(C_GOLD, C_BG);
  tft.setTextSize(2);
  tft.setCursor(10, 58);  tft.print("SLH-Device");
  tft.setTextColor(TFT_WHITE, C_BG);
  tft.setTextSize(1);
  tft.setCursor(10, 85);  tft.print("Then open browser:");
  tft.setTextColor(TFT_CYAN, C_BG);
  tft.setCursor(10, 100); tft.print("192.168.4.1");
  tft.setTextColor(TFT_WHITE, C_BG);
  tft.setCursor(10, 120); tft.print("Enter your home WiFi creds.");
  drawStatus("Waiting for WiFi config...", C_GRAY);
}

void drawQR(const String& url) {
  tft.fillScreen(C_BG);
  drawHeader("Pair Device");

  QRCode qrcode;
  uint8_t qrData[qrcode_getBufferSize(3)];
  qrcode_initText(&qrcode, qrData, 3, ECC_LOW, url.c_str());

  int px = 4;
  int sz = qrcode.size * px;
  int ox = 10;
  int oy = 35;

  tft.fillRect(ox - 4, oy - 4, sz + 8, sz + 8, TFT_WHITE);
  for (uint8_t y = 0; y < qrcode.size; y++) {
    for (uint8_t x = 0; x < qrcode.size; x++) {
      uint16_t c = qrcode_getModule(&qrcode, x, y) ? TFT_BLACK : TFT_WHITE;
      tft.fillRect(ox + x * px, oy + y * px, px, px, c);
    }
  }

  int tx = ox + sz + 14;
  tft.setTextColor(TFT_WHITE, C_BG);
  tft.setTextSize(1);
  tft.setCursor(tx, 40);  tft.print("Scan QR code");
  tft.setCursor(tx, 56);  tft.print("to pair your");
  tft.setCursor(tx, 72);  tft.print("SLH wallet.");
  tft.setCursor(tx, 96);  tft.setTextColor(C_GRAY, C_BG); tft.print("ID:");
  tft.setCursor(tx, 108); tft.print(g_device_id.substring(4, 12));

  drawStatus("Waiting for pairing...", C_GRAY);
}

void drawBalances(JsonObject bal) {
  tft.fillScreen(C_BG);
  drawHeader("My Wallet");

  struct TokenRow { const char* key; uint16_t color; } rows[] = {
    {"SLH", C_GOLD},
    {"ZVK", TFT_GREEN},
    {"MNH", TFT_WHITE},
    {"REP", TFT_BLUE},
    {"ZUZ", TFT_RED},
  };

  int y = 36;
  for (auto& r : rows) {
    float v = bal[r.key] | 0.0f;
    tft.setTextColor(r.color, C_BG);
    tft.setTextSize(2);
    tft.setCursor(10, y);
    tft.print(r.key);
    tft.print(":");
    tft.setTextColor(TFT_WHITE, C_BG);
    tft.setCursor(80, y);
    tft.print(v, r.key[0] == 'S' ? 4 : 0);  // SLH shows 4 decimals
    y += 36;
  }

  char ts[32];
  snprintf(ts, sizeof(ts), "uid:%d  up:%lus", g_user_id, millis() / 1000);
  drawStatus(ts, C_GRAY);
}

// ─── API calls ────────────────────────────────────────────────
bool pollClaim() {
  if (WiFi.status() != WL_CONNECTED) return false;
  HTTPClient http;
  http.begin(String(API_BASE) + "/api/device/claim/" + g_device_id);
  http.setTimeout(8000);
  int code = http.GET();
  bool paired = false;
  if (code == 200) {
    JsonDocument doc;
    deserializeJson(doc, http.getString());
    if (doc["paired"].as<bool>()) {
      g_signing_token = doc["signing_token"].as<String>();
      g_user_id       = doc["user_id"].as<int>();
      saveToken(g_signing_token, g_user_id);
      paired = true;
    }
  }
  http.end();
  return paired;
}

void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED || g_signing_token.isEmpty()) return;
  HTTPClient http;
  http.begin(String(API_BASE) + "/api/esp/heartbeat");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + g_signing_token);
  http.setTimeout(8000);
  JsonDocument doc;
  doc["device_id"]      = g_device_id;
  doc["fw"]             = SLH_FW_TAG;
  doc["ssid"]           = WiFi.SSID();
  doc["rssi"]           = WiFi.RSSI();
  doc["ip"]             = WiFi.localIP().toString();
  doc["uptime_seconds"] = (int)(millis() / 1000);
  doc["free_heap"]      = (int)ESP.getFreeHeap();
  String body; serializeJson(doc, body);
  http.POST(body);
  http.end();
}

void fetchBalances() {
  if (WiFi.status() != WL_CONNECTED || g_signing_token.isEmpty()) return;
  HTTPClient http;
  http.begin(String(API_BASE) + "/api/wallet/" + String(g_user_id) + "/balances");
  http.addHeader("Authorization", "Bearer " + g_signing_token);
  http.setTimeout(8000);
  int code = http.GET();
  if (code == 200) {
    JsonDocument doc;
    deserializeJson(doc, http.getString());
    JsonObject bal = doc["balances"].as<JsonObject>();
    if (!bal.isNull()) drawBalances(bal);
    else drawStatus("Balances empty", C_GRAY);
  } else {
    char msg[32];
    snprintf(msg, sizeof(msg), "Balance fetch: HTTP %d", code);
    drawStatus(msg, TFT_RED);
  }
  http.end();
}

void pollCommands() {
  if (WiFi.status() != WL_CONNECTED || g_signing_token.isEmpty()) return;
  HTTPClient http;
  http.begin(String(API_BASE) + "/api/esp/commands/" + g_device_id);
  http.addHeader("Authorization", "Bearer " + g_signing_token);
  http.setTimeout(5000);
  if (http.GET() == 200) {
    JsonDocument doc;
    deserializeJson(doc, http.getString());
    String cmd = doc["command"] | "";
    if (cmd == "REBOOT") {
      drawStatus("Admin: REBOOT", TFT_RED);
      delay(1000); ESP.restart();
    } else if (cmd == "CLEAR_TOKEN") {
      prefs.begin("slh", false); prefs.clear(); prefs.end();
      ESP.restart();
    }
  }
  http.end();
}

// ─── Setup ───────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Backlight + display init
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);
  tft.init();
  tft.setRotation(1);  // landscape
  drawBootScreen();

  g_device_id = makeDeviceId();
  Serial.printf("[SLH] device=%s fw=%s\n", g_device_id.c_str(), SLH_FW_TAG);

  loadPrefs();

  // WiFi — captive portal on first boot, auto-reconnect thereafter
  WiFiManager wm;
  wm.setConfigPortalTimeout(180);
  wm.setAPCallback([](WiFiManager*) { drawWiFiSetupScreen(); });
  if (!wm.autoConnect("SLH-Device")) {
    drawStatus("WiFi timeout. Restarting.", TFT_RED);
    delay(2000); ESP.restart();
  }

  drawStatus("WiFi connected!", TFT_GREEN);
  Serial.printf("[SLH] wifi=%s ip=%s\n", WiFi.SSID().c_str(), WiFi.localIP().toString().c_str());

  if (g_signing_token.isEmpty()) {
    String qrUrl = String(SLH_PAIR_URL) + "?mac=" + getMacStr() + "&device_id=" + g_device_id;
    Serial.printf("[SLH] QR: %s\n", qrUrl.c_str());
    drawQR(qrUrl);
    g_state = PAIRING;
  } else {
    g_state = PAIRED;
    drawStatus("Loading balances...", TFT_GREEN);
    fetchBalances();
  }
}

// ─── Loop ────────────────────────────────────────────────────
void loop() {
  uint32_t now = millis();

  if (g_state == PAIRING) {
    if (now - g_last_claim >= CLAIM_INTERVAL_MS) {
      g_last_claim = now;
      if (pollClaim()) {
        drawStatus("Paired! Loading wallet...", TFT_GREEN);
        delay(800);
        g_state = PAIRED;
        fetchBalances();
      }
    }
    return;
  }

  if (g_state == PAIRED) {
    if (now - g_last_heartbeat >= HEARTBEAT_INTERVAL_MS) {
      g_last_heartbeat = now;
      sendHeartbeat();
      pollCommands();
    }
    if (now - g_last_balance >= BALANCE_INTERVAL_MS) {
      g_last_balance = now;
      fetchBalances();
    }
  }
}

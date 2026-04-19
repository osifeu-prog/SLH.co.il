// =====================================================================
// SLH WALLET — ESP32 CYD (Cheap Yellow Display, ILI9341 320x240)
// =====================================================================
// Live view of Osif's kosher wallet on Railway API.
// - Polls /api/user/{telegram_id}       -> SLH / ZVK / MNH balances
// - Polls /api/external-wallets/{id}    -> on-chain TON / BNB
// - Refreshes every 30s, or on BTN1 short press
// - BTN2 short press cycles display mode: TOKENS -> ONCHAIN -> STATUS
//
// NOTE on fonts:
//   TFT_eSPI with LOAD_FONT2/LOAD_GLCD (see platformio.ini) cannot render
//   Hebrew glyphs out of the box — no RTL shaping, no Unicode font atlas.
//   All on-screen text is therefore English/Latin. Osif's original ask
//   was "מתחבר..." which we render as "Connecting..." for that reason.
//   If Hebrew display is required later, switch to LVGL + Noto Sans Hebrew
//   or a custom TTF via TFT_eSPI smooth fonts.
//
// Pins + TFT init mirror main_advanced.cpp so we stay on the same CYD
// hardware profile.
// =====================================================================

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>

#include "wifi_secrets.h"
#include "led_controller.h"
#include "button_handler.h"

// ===== Pins (match main_advanced.cpp) =====
static const int PIN_BL = 21;

// ===== Display mode enum =====
enum DisplayMode {
    MODE_TOKENS = 0,
    MODE_ONCHAIN = 1,
    MODE_STATUS = 2,
    MODE_COUNT = 3
};

// ===== Globals =====
TFT_eSPI tft = TFT_eSPI();
LedController ledController;
DualButtonHandler buttonHandler;

static DisplayMode displayMode = MODE_TOKENS;
static unsigned long lastRefresh = 0;
static const unsigned long REFRESH_INTERVAL_MS = 30000UL;

// Last-known wallet data (kept in RAM between refreshes)
struct WalletSnapshot {
    bool valid = false;
    float slh = 0.0f;
    float zvk = 0.0f;
    float mnh = 0.0f;
    float ton_internal = 0.0f;   // TON_available from /api/user
    float ton_onchain = 0.0f;    // from /api/external-wallets (network=ton)
    float bnb_onchain = 0.0f;    // from /api/external-wallets (network=bsc)
    String errorTag = "";        // "", "NO WIFI", "API DOWN", "AUTH ERR", "PARSE ERR"
    unsigned long fetchedAtMs = 0;
};
static WalletSnapshot wallet;

// ===== UI helpers (preserve drawCentered signature from main_advanced.cpp) =====
void drawCentered(const String& text, int y, int font = 2, uint16_t color = TFT_WHITE) {
    tft.setTextDatum(MC_DATUM);
    tft.setTextColor(color, TFT_BLACK);
    // Display is 320x240 in landscape (rotation=1), so center X = 160
    tft.drawString(text, 160, y, font);
}

void drawLeft(const String& text, int x, int y, int font = 2, uint16_t color = TFT_WHITE) {
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(color, TFT_BLACK);
    tft.drawString(text, x, y, font);
}

void drawRight(const String& text, int x, int y, int font = 2, uint16_t color = TFT_WHITE) {
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(color, TFT_BLACK);
    tft.drawString(text, x, y, font);
}

// Format a float with K/M suffix so 199788 shows as "199.79K"
String humanNum(float v) {
    char buf[32];
    if (v >= 1000000.0f) {
        snprintf(buf, sizeof(buf), "%.2fM", v / 1000000.0f);
    } else if (v >= 1000.0f) {
        snprintf(buf, sizeof(buf), "%.2fK", v / 1000.0f);
    } else if (v >= 1.0f) {
        snprintf(buf, sizeof(buf), "%.2f", v);
    } else if (v > 0.0f) {
        snprintf(buf, sizeof(buf), "%.6f", v);
    } else {
        snprintf(buf, sizeof(buf), "0");
    }
    return String(buf);
}

// ===== Drawing: header + body per mode =====
void drawHeader(const char* subtitle, uint16_t subColor) {
    tft.fillRect(0, 0, 320, 50, TFT_BLACK);
    drawCentered("SLH WALLET", 14, 4, TFT_CYAN);
    drawCentered(subtitle, 38, 2, subColor);
    // separator line
    tft.drawFastHLine(10, 50, 300, TFT_DARKGREY);
}

void drawFooter(const char* hint) {
    tft.fillRect(0, 218, 320, 22, TFT_BLACK);
    drawCentered(hint, 228, 1, TFT_DARKGREY);
}

void drawModeTokens() {
    tft.fillRect(0, 55, 320, 160, TFT_BLACK);

    int y = 72;
    const int xLabel = 20;
    const int xValue = 300;
    const int rowH = 34;

    drawLeft("SLH",  xLabel, y,              4, TFT_GOLD);
    drawRight(humanNum(wallet.slh), xValue, y,              4, TFT_WHITE);

    drawLeft("ZVK",  xLabel, y + rowH,       4, TFT_GREEN);
    drawRight(humanNum(wallet.zvk), xValue, y + rowH,       4, TFT_WHITE);

    drawLeft("MNH",  xLabel, y + rowH * 2,   4, TFT_SKYBLUE);
    drawRight(humanNum(wallet.mnh), xValue, y + rowH * 2,   4, TFT_WHITE);

    drawLeft("TON (internal)", xLabel, y + rowH * 3 + 6, 2, TFT_LIGHTGREY);
    drawRight(humanNum(wallet.ton_internal), xValue, y + rowH * 3 + 6, 2, TFT_WHITE);
}

void drawModeOnchain() {
    tft.fillRect(0, 55, 320, 160, TFT_BLACK);

    int y = 80;
    const int xLabel = 20;
    const int xValue = 300;
    const int rowH = 42;

    drawLeft("TON",  xLabel, y,              4, TFT_BLUE);
    drawRight(humanNum(wallet.ton_onchain), xValue, y,              4, TFT_WHITE);

    drawLeft("BNB",  xLabel, y + rowH,       4, TFT_YELLOW);
    drawRight(humanNum(wallet.bnb_onchain), xValue, y + rowH,       4, TFT_WHITE);

    drawLeft("(on-chain, cached)", xLabel, y + rowH * 2 + 10, 2, TFT_DARKGREY);
}

void drawModeStatus() {
    tft.fillRect(0, 55, 320, 160, TFT_BLACK);

    int y = 64;
    const int rowH = 22;

    String wifiLine = (WiFi.status() == WL_CONNECTED)
        ? String("WiFi: ") + WiFi.SSID()
        : String("WiFi: DISCONNECTED");
    drawLeft(wifiLine, 12, y, 2, (WiFi.status() == WL_CONNECTED) ? TFT_GREEN : TFT_RED);

    String ipLine = (WiFi.status() == WL_CONNECTED)
        ? String("IP:   ") + WiFi.localIP().toString()
        : String("IP:   --");
    drawLeft(ipLine, 12, y + rowH, 2, TFT_WHITE);

    char rssiBuf[32];
    snprintf(rssiBuf, sizeof(rssiBuf), "RSSI: %d dBm", WiFi.RSSI());
    drawLeft(rssiBuf, 12, y + rowH * 2, 2, TFT_WHITE);

    char heapBuf[32];
    snprintf(heapBuf, sizeof(heapBuf), "Heap: %u bytes", (unsigned) ESP.getFreeHeap());
    drawLeft(heapBuf, 12, y + rowH * 3, 2, TFT_WHITE);

    unsigned long ageSec = wallet.fetchedAtMs == 0 ? 0 : (millis() - wallet.fetchedAtMs) / 1000;
    char ageBuf[40];
    snprintf(ageBuf, sizeof(ageBuf), "Data age: %lus", ageSec);
    drawLeft(ageBuf, 12, y + rowH * 4, 2, TFT_WHITE);

    if (wallet.errorTag.length() > 0) {
        drawLeft(String("Err:  ") + wallet.errorTag, 12, y + rowH * 5, 2, TFT_RED);
    } else {
        drawLeft("Err:  OK", 12, y + rowH * 5, 2, TFT_GREEN);
    }
}

void redrawFull() {
    tft.fillScreen(TFT_BLACK);
    const char* sub = "TOKENS";
    uint16_t subColor = TFT_GOLD;
    if (displayMode == MODE_ONCHAIN) { sub = "ON-CHAIN"; subColor = TFT_BLUE; }
    else if (displayMode == MODE_STATUS)  { sub = "STATUS";   subColor = TFT_MAGENTA; }
    drawHeader(sub, subColor);

    if (wallet.errorTag.length() > 0 && displayMode != MODE_STATUS) {
        // Big error banner over body area
        tft.fillRect(0, 55, 320, 160, TFT_BLACK);
        drawCentered(wallet.errorTag, 130, 4, TFT_RED);
        drawCentered("BTN1=retry  BTN2=switch view", 180, 2, TFT_DARKGREY);
    } else {
        switch (displayMode) {
            case MODE_TOKENS:  drawModeTokens();  break;
            case MODE_ONCHAIN: drawModeOnchain(); break;
            case MODE_STATUS:  drawModeStatus();  break;
            default: break;
        }
    }

    drawFooter("BTN1=refresh   BTN2=cycle view");
}

// ===== WiFi =====
bool connectWiFi(unsigned long timeoutMs = 20000) {
    Serial.printf("[WIFI] connecting to %s ...\n", WIFI_SSID);
    drawCentered("Connecting...", 130, 4, TFT_YELLOW);  // was "מתחבר..." — TFT_eSPI cannot render Hebrew
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - start > timeoutMs) {
            Serial.println("[WIFI] timeout");
            return false;
        }
        delay(250);
    }
    Serial.printf("[WIFI] connected ip=%s rssi=%d\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    return true;
}

// ===== HTTP helpers =====
// Returns HTTP code, or -1 on transport error. Fills `body`.
int httpsGet(const String& url, String& body) {
    WiFiClientSecure client;
    client.setInsecure(); // skip cert validation — Railway cert changes; device has no CA store
    HTTPClient http;
    http.setTimeout(10000);
    if (!http.begin(client, url)) {
        Serial.println("[HTTP] begin failed");
        return -1;
    }
    int code = http.GET();
    if (code > 0) {
        body = http.getString();
    }
    http.end();
    return code;
}

// Parse /api/user/{id} response into wallet fields.
// Response shape (inspected in main.py /api/user/{telegram_id}):
//   {
//     "user":    {...},
//     "balances":{"SLH":..., "ZVK":..., "MNH":..., "TON_available":..., "TON_locked":...},
//     "premium": bool, "deposits":[], "staking":[]
//   }
bool parseUserBalances(const String& body) {
    // Large doc — /api/user can include deposits + staking arrays
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, body);
    if (err) {
        Serial.printf("[JSON] user parse err=%s\n", err.c_str());
        return false;
    }
    JsonObject bal = doc["balances"].as<JsonObject>();
    if (bal.isNull()) {
        Serial.println("[JSON] balances missing");
        return false;
    }
    wallet.slh          = bal["SLH"]           | 0.0f;
    wallet.zvk          = bal["ZVK"]           | 0.0f;
    wallet.mnh          = bal["MNH"]           | 0.0f;
    wallet.ton_internal = bal["TON_available"] | 0.0f;
    return true;
}

// Parse /api/external-wallets/{id} and fill on-chain TON + BNB.
// Shape: { "user_id": ..., "wallets": [ {"network":"ton|bsc", "last_balance_native":..., ...}, ... ] }
bool parseExternalWallets(const String& body) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, body);
    if (err) {
        Serial.printf("[JSON] external parse err=%s\n", err.c_str());
        return false;
    }
    wallet.ton_onchain = 0.0f;
    wallet.bnb_onchain = 0.0f;
    JsonArray arr = doc["wallets"].as<JsonArray>();
    if (arr.isNull()) return true; // empty wallet list is fine
    for (JsonObject w : arr) {
        const char* net = w["network"] | "";
        float nat = w["last_balance_native"] | 0.0f;
        if (strcmp(net, "ton") == 0) {
            wallet.ton_onchain += nat;
        } else if (strcmp(net, "bsc") == 0 || strcmp(net, "bnb") == 0 || strcmp(net, "eth") == 0) {
            // BSC wallet native balance is BNB
            wallet.bnb_onchain += nat;
        }
    }
    return true;
}

void doRefresh() {
    if (WiFi.status() != WL_CONNECTED) {
        wallet.errorTag = "NO WIFI";
        ledController.solid("red");
        redrawFull();
        return;
    }

    ledController.solid("blue");

    // 1) /api/user/{id}
    char urlUser[160];
    snprintf(urlUser, sizeof(urlUser),
             "%s/api/user/%llu", SLH_API_BASE, (unsigned long long) SLH_TELEGRAM_ID);
    String body;
    int code = httpsGet(String(urlUser), body);
    Serial.printf("[HTTP] GET %s -> %d (%u bytes)\n", urlUser, code, body.length());

    if (code == 401 || code == 403) {
        wallet.errorTag = "AUTH ERR";
        ledController.solid("red");
        redrawFull();
        return;
    }
    if (code < 200 || code >= 300) {
        wallet.errorTag = "API DOWN";
        ledController.solid("red");
        redrawFull();
        return;
    }
    if (!parseUserBalances(body)) {
        wallet.errorTag = "PARSE ERR";
        ledController.solid("red");
        redrawFull();
        return;
    }

    // 2) /api/external-wallets/{id}  (non-fatal if this fails)
    char urlExt[180];
    snprintf(urlExt, sizeof(urlExt),
             "%s/api/external-wallets/%llu", SLH_API_BASE, (unsigned long long) SLH_TELEGRAM_ID);
    String extBody;
    int extCode = httpsGet(String(urlExt), extBody);
    Serial.printf("[HTTP] GET %s -> %d (%u bytes)\n", urlExt, extCode, extBody.length());
    if (extCode >= 200 && extCode < 300) {
        parseExternalWallets(extBody);
    }
    // If external fails we keep last known on-chain values and move on.

    wallet.valid = true;
    wallet.errorTag = "";
    wallet.fetchedAtMs = millis();
    ledController.solid("green");
    redrawFull();
}

// ===== Button callbacks =====
void onShortPress(const char* btn) {
    if (String(btn) == "BTN1") {
        Serial.println("[UI] BTN1 short -> force refresh");
        doRefresh();
    } else {
        displayMode = (DisplayMode) ((displayMode + 1) % MODE_COUNT);
        Serial.printf("[UI] BTN2 short -> mode=%d\n", (int) displayMode);
        redrawFull();
    }
}

void onLongPress(const char* btn) {
    Serial.printf("[UI] %s long -> reboot soft\n", btn);
    ledController.solid("yellow");
    delay(200);
    ESP.restart();
}

// ===== setup / loop =====
void setup() {
    Serial.begin(115200);
    delay(800);
    Serial.println();
    Serial.println("[BOOT] fw=slh-wallet");

    pinMode(PIN_BL, OUTPUT);
    digitalWrite(PIN_BL, HIGH);

    tft.init();
    tft.setRotation(1);       // landscape 320x240
    digitalWrite(PIN_BL, HIGH);
    tft.fillScreen(TFT_BLACK);
    drawHeader("Booting...", TFT_YELLOW);

    ledController.init();
    ledController.solid("yellow");

    buttonHandler.init();
    buttonHandler.onShortPress(onShortPress);
    buttonHandler.onLongPress(onLongPress);

    if (!connectWiFi()) {
        wallet.errorTag = "NO WIFI";
        ledController.solid("red");
        redrawFull();
    } else {
        doRefresh();
    }
}

void loop() {
    buttonHandler.update();
    ledController.update();

    // Auto-refresh every 30s
    if (millis() - lastRefresh > REFRESH_INTERVAL_MS) {
        lastRefresh = millis();
        doRefresh();
    }

    // If STATUS view is showing, redraw every ~2s so uptime / RSSI stay fresh
    static unsigned long lastStatusTick = 0;
    if (displayMode == MODE_STATUS && millis() - lastStatusTick > 2000) {
        lastStatusTick = millis();
        drawModeStatus();
    }

    delay(10);
}

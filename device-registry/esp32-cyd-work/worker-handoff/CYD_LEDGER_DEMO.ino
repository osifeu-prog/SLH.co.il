#include <SPI.h>
#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

static const int TFT_BL = 21;
static const int BTN1   = 32;
static const int BTN2   = 33;
static const int LED_R  = 25;
static const int LED_G  = 16;
static const int LED_B  = 17;

int screenIndex = 0;
int lightMode = 0;

void setRGB(int r, int g, int b) {
  ledcWrite(LED_R, 255 - r);
  ledcWrite(LED_G, 255 - g);
  ledcWrite(LED_B, 255 - b);
}

void applyLightMode() {
  switch (lightMode) {
    case 0: setRGB(0, 0, 255); break;        // BLUE
    case 1: setRGB(255, 0, 0); break;        // RED
    case 2: setRGB(0, 255, 0); break;        // GREEN
    case 3: setRGB(255, 255, 255); break;    // WHITE
    case 4: setRGB(0, 0, 0); break;          // OFF
  }
}

void drawHeader(const char* title) {
  tft.fillScreen(TFT_BLACK);
  tft.fillRect(0, 0, 320, 28, TFT_DARKGREY);
  tft.setTextColor(TFT_YELLOW, TFT_DARKGREY);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(title, 160, 14, 2);
}

void drawBoot() {
  drawHeader("SLH SPARK");
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawCentreString("SLH", 160, 60, 4);
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawCentreString("LEDGER DEVICE", 160, 110, 2);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawCentreString("ESP32 CYD DEMO", 160, 150, 2);
}

void drawHome() {
  drawHeader("HOME");
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Product:", 20, 50, 2);
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("SLH Ledger Node", 120, 50, 2);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Price:", 20, 90, 2);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("888 ILS", 120, 90, 2);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("BTN1 -> Next", 20, 170, 2);
  tft.drawString("BTN2 -> Light", 20, 200, 2);
}

void drawWallet() {
  drawHeader("WALLET");
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Owner:", 20, 50, 2);
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("OSIF", 120, 50, 2);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("SLH:", 20, 90, 2);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawString("199788", 120, 90, 2);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("TON:", 20, 130, 2);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawString("0", 120, 130, 2);

  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Demo values", 20, 200, 2);
}

void drawLedger() {
  drawHeader("LEDGER");
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Status:", 20, 50, 2);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawString("ONLINE", 120, 50, 2);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Node ID:", 20, 90, 2);
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("SLH-001", 120, 90, 2);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("Role:", 20, 130, 2);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Member Ledger", 120, 130, 2);
}

void drawLighting() {
  drawHeader("LIGHTING");
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("BTN2 cycles modes", 20, 60, 2);
  tft.drawString("Mode:", 20, 110, 2);

  const char* names[] = {"BLUE", "RED", "GREEN", "WHITE", "OFF"};
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString(names[lightMode], 120, 110, 2);
}

void renderScreen() {
  switch (screenIndex) {
    case 0: drawBoot(); break;
    case 1: drawHome(); break;
    case 2: drawWallet(); break;
    case 3: drawLedger(); break;
    case 4: drawLighting(); break;
    default: drawHome(); break;
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);

  pinMode(BTN1, INPUT_PULLUP);
  pinMode(BTN2, INPUT_PULLUP);

  ledcAttach(LED_R, 5000, 8);
  ledcAttach(LED_G, 5000, 8);
  ledcAttach(LED_B, 5000, 8);

  tft.init();
  tft.setRotation(1);

  applyLightMode();
  renderScreen();
}

void loop() {
  static int lastBtn1 = HIGH;
  static int lastBtn2 = HIGH;

  int b1 = digitalRead(BTN1);
  int b2 = digitalRead(BTN2);

  if (lastBtn1 == HIGH && b1 == LOW) {
    screenIndex++;
    if (screenIndex > 4) screenIndex = 0;
    renderScreen();
    delay(220);
  }

  if (lastBtn2 == HIGH && b2 == LOW) {
    lightMode++;
    if (lightMode > 4) lightMode = 0;
    applyLightMode();
    if (screenIndex == 4) renderScreen();
    delay(220);
  }

  lastBtn1 = b1;
  lastBtn2 = b2;
  delay(30);
}

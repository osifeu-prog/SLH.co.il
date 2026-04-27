#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

String cmd = "";
bool toggle = false;

void drawUI() {
  tft.fillScreen(TFT_BLACK);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("SLH CONTROL NODE", 10, 10, 2);

  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawString("STATUS: ACTIVE", 10, 40, 2);

  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("CMD: " + cmd, 10, 80, 2);
}

void handleCommand(String c) {
  c.trim();

  if (c == "RED") {
    tft.fillScreen(TFT_RED);
  } 
  else if (c == "GREEN") {
    tft.fillScreen(TFT_GREEN);
  } 
  else if (c == "BLUE") {
    tft.fillScreen(TFT_BLUE);
  } 
  else if (c == "UI") {
    drawUI();
  } 
  else if (c == "PING") {
    Serial.println("PONG");
  } 
  else {
    Serial.println("UNKNOWN CMD");
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  tft.init();
  tft.setRotation(1);

  pinMode(21, OUTPUT);
  digitalWrite(21, HIGH);

  drawUI();

  Serial.println("SLH READY");
}

void loop() {
  if (Serial.available()) {
    cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
    drawUI();
  }

  delay(100);
}

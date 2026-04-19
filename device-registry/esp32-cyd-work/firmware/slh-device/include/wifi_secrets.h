#pragma once

// =====================================================================
// SLH WALLET — Wi-Fi credentials
// =====================================================================
// Fill these in before flashing main_wallet.cpp to the ESP32.
// This file is intentionally gitignored / never committed.
//
// Osif: replace the placeholders below with your real home Wi-Fi
// SSID and password, then run UPLOAD_WALLET.ps1.
// =====================================================================

#define WIFI_SSID     "PLACEHOLDER_SSID"
#define WIFI_PASSWORD "PLACEHOLDER_PASSWORD"

// Telegram ID whose wallet the device will display.
// 224223270 = Osif Kaufman Ungar
#define SLH_TELEGRAM_ID 224223270ULL

// API host (no trailing slash). Railway production.
#define SLH_API_BASE "https://slh-api-production.up.railway.app"

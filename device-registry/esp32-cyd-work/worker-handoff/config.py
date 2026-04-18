WIFI_SSID = 'Beynoni'
WIFI_PASS = '12345678'
TON_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd'
UPDATE_INTERVAL = 30

# CYD (ESP32-2432S024R) pinout
PINS = {
    'SCK': 14,
    'MOSI': 13,
    'MISO': 12,   # used as RST
    'CS': 15,
    'DC': 2,
    'RST': 12,
    'BL': 21
}

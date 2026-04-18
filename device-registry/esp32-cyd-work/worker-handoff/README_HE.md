# SLH ESP32 CYD — Worker Handoff

## נתיב מקור
D:\ARCHIVE_SLH_OLD\SLH_PROJECT_V2_20260416\ESP

## נתיב עבודה נקי
D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-cyd-clean

## חומרה מאושרת
- דגם: ESP32-2432S028R (CYD)
- תצוגה: ILI9341 240x320 SPI
- LED RGB: R=25, G=16, B=17
- כפתורים: BTN1=32, BTN2=33
- Backlight: GPIO 21

## פיני תצוגה
- SCK=14
- MOSI=13
- MISO=12
- CS=15
- DC=2
- RST=-1 בארדואינו / 12 במיקרופייתון
- BL=21
- SPI=27MHz

## קבצים עיקריים
- CYD_LEDGER_DEMO.ino
- User_Setup_SLH_CYD.h
- color_test.py
- config.py
- hardware_profile.json
- upload.ps1
- firmware[bin]2.bin

## תנאי מעבר לשלב הבא
חובה לאשר שה-color_test עובד על המכשיר:
1. אדום
2. ירוק
3. כחול
4. טקסט: SLH TEST

## שלב עבודה מומלץ
1. לאשר color_test פיזית על המסך
2. לקבע TFT config לפי User_Setup_SLH_CYD.h
3. רק אז לעבור ל-E.2+

## PlatformIO
נכתב קובץ platformio.ini נקי בתוך:
D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-cyd-clean

## הערה חשובה
אין לדרוס ספריות מערכת בלי גיבוי.
אם צריך להעתיק User_Setup_SLH_CYD.h ל-TFT_eSPI library folder, לבצע זאת ידנית ורק אחרי אימות הנתיב.

## פקודות בסיס
Set-Location "D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-cyd-clean"
pio run
pio run -t upload --upload-port COM5
pio device monitor -p COM5 -b 115200

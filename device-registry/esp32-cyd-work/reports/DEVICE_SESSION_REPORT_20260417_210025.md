# Device Session Report - 2026-04-17 21:00:25

## Facts confirmed
- Active serial port: COM5
- Device outputs boot logs on COM5
- Existing firmware on device is old/broken
- Build currently blocked by pyreadline + SCons issue

## Errors observed
- Preferences begin(): nvs_open failed: NOT_FOUND
- WiFiSTA begin(): SSID too long or missing!
- PlatformIO build crash due to pyreadline using collections.Callable

## Decisions
- Move to stable clean boot firmware
- Add calm light mapping mode
- Increase font sizes
- Prepare demo-page integration plan

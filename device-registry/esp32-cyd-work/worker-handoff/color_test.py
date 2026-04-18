import machine, time, ili9341
from machine import Pin, SPI

# CYD pins
SCK=14; MOSI=13; MISO=12; CS=15; DC=2; RST=12; BL=21

# Backlight on
Pin(BL, Pin.OUT).value(1)

# Reset
rst = Pin(RST, Pin.OUT)
rst.value(0); time.sleep(0.1); rst.value(1); time.sleep(0.1)

# SPI (full duplex as in cyd_fix)
spi = SPI(2, baudrate=20000000, sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))
display = ili9341.ILI9341(spi, cs=Pin(CS), dc=Pin(DC), rst=Pin(RST))
display.set_rotation(1)

print("Red")
display.fill(0xF800)
time.sleep(2)

print("Green")
display.fill(0x07E0)
time.sleep(2)

print("Blue")
display.fill(0x001F)
time.sleep(2)

print("White text on black")
display.fill(0x0000)
display.text("SLH TEST", 100, 100, 0xFFFF)
time.sleep(3)

print("Done")

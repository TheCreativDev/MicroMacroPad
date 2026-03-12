"""
Macropad Firmware mit OLED Display
Board: XIAO RP2040
Layout: 2x3 Matrix + 2 Rotary Encoders + 0.91" 128x32 OLED Display
"""

import board
import busio
import time

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.modules.encoder import EncoderHandler

# OLED Display
try:
    import adafruit_ssd1306
    from PIL import Image, ImageDraw
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False

keyboard = KMKKeyboard()

keyboard.row_pins = (
    board.GP3,
    board.GP2,
)

keyboard.col_pins = (
    board.GP1,
    board.GP0,
    board.GP6,
)

keyboard.diode_orientation = DiodeOrientation.COL2ROW

encoder_handler = EncoderHandler()

encoder_handler.pins = (
    (board.GP10, board.GP9),  # Encoder 1
    (board.GP8, board.GP7),  # Encoder 2
)

"""
Format:
((CCW, CW),(CCW,CW))

CCW = counter clockwise
CW  = clockwise
"""

encoder_handler.map = (
    ((KC.VOLD, KC.VOLU)),      # Encoder 1 Lautstärke
    ((KC.LEFT, KC.RIGHT)),     # Encoder 2 Cursor
)

keyboard.modules.append(encoder_handler)

if DISPLAY_AVAILABLE:
    # I2C Pins: SCL=GP5, SDA=GP4
    i2c = busio.I2C(board.GP5, board.GP4)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)
    
    # Wave Effekt Config
    wave_active = False
    wave_start_time = 0.0
    wave_duration = 0.5  # sek
    
    def trigger_wave():
        global wave_active, wave_start_time
        wave_active = True
        wave_start_time = time.monotonic()
    
    def render_wave():
        global wave_active
        
        if not wave_active:
            return
        
        current_time = time.monotonic()
        elapsed = current_time - wave_start_time
        
        if elapsed >= wave_duration:
            wave_active = False
            oled.fill(0)
            oled.show()
            return
        
        # Farbiges Bild erstellen (RGB für rote Welle)
        image = Image.new("RGB", (128, 32), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Wellenausbreitung berechnen
        progress = elapsed / wave_duration  # 0.0 - 1.0
        max_expansion = 64  # Hälfte der Breite
        wave_width = int(progress * max_expansion)
        
        # Helligkeit abdimmen
        brightness = 255 * (1 - (progress)**2)
        
        center_x = 64  # Mitte des Displays
        
        # Welle zeichnen wenn sichtbar
        if brightness > 20:
            # Rote Farbe mit Helligkeit
            red_value = int(brightness)
            red_color = (red_value, 0, 0)
            
            # Linke Seite, expandiert nach links
            for dx in range(max(0, wave_width)):
                x = center_x - dx
                if 0 <= x < 128:
                    draw.line([(x, 0), (x, 31)], fill=red_color)
            
            # Rechte Seite, expandiert nach rechts
            for dx in range(max(0, wave_width)):
                x = center_x + dx
                if 0 <= x < 128:
                    draw.line([(x, 0), (x, 31)], fill=red_color)
                     
        
        # Bild auf Display anzeigen
        oled.image(image)
        oled.show()
    
    # Hook: Wave bei Tastendrücken triggern
    original_process_key = keyboard.process_key
    
    def new_process_key(key, is_pressed, int_coord):
        trigger_wave()
        return original_process_key(key, is_pressed, int_coord)
    
    keyboard.process_key = new_process_key

keyboard.keymap = [
    [
        KC.MUTE,   KC.PLAY,   KC.NEXT,     # obere Reihe
        KC.A,      KC.B,      KC.C         # untere Reihe
    ]
]

if __name__ == '__main__':
    if DISPLAY_AVAILABLE:
        oled.fill(0)
        oled.show()
    
    # Main Loop
    keyboard.go()
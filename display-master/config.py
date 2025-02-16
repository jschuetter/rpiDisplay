#!/bin/python
'''
config.py
Config options & settings for LED matrix and modules
Updated 16 Feb 2025
'''
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from dotenv import load_dotenv
import os, webcolors

FONTS_PATH = "fonts/"

# Address of default second terminal in VSCode remote environment
# Not currently in use
VSCODE_ALT_TERMINAL = "/dev/pts/2" 

# Log file path
LOG_FILE = "output.log"

# Default module values
DEF_DELAY = 0.1 # Default delay between module frames
DEF_DOLOOP = 1 # Default loop boolean (loop methods enabled by default)

def matrix_from_env() -> RGBMatrix:
    # Load environment vars, create options object
    load_dotenv()
    options = RGBMatrixOptions()

    options.hardware_mapping = os.getenv("GPIO_MAPPING", "regular")
    options.panel_type = os.getenv("LED_PANEL_TYPE", "")
    options.rows = int(os.getenv("MATRIX_ROWS", 32))
    options.cols = int(os.getenv("MATRIX_COLS", 32))
    options.chain_length = int(os.getenv("CHAIN_LENGTH", 1))
    options.parallel = int(os.getenv("PARALLEL", 1))
    options.multiplexing = int(os.getenv("MUX", 0))
    options.pixel_mapper_config = os.getenv("PX_MAP", "")
    options.pwm_bits = int(os.getenv("PWM_BITS", 11))
    options.scan_mode = int(os.getenv("SCAN_MODE", 0))
    options.row_address_type =  int(os.getenv("ADDR_TYPE", 0))
    options.inverse_colors = int(os.getenv("INVERT_COLORS", 0))
    options.led_rgb_sequence = os.getenv("RGB_SEQ", "RGB")
    options.pwm_lsb_nanoseconds = int(os.getenv("PWM_LSB_NS", 130))
    options.pwm_dither_bits = int(os.getenv("PWM_DITHER_BITS", 0))
    options.show_refresh_rate = int(os.getenv("SHOW_REFRESH", 0))
    options.limit_refresh_rate_hz = int(os.getenv("LIMIT_REFRESH", 0))
    options.brightness = int(os.getenv("BRIGHTNESS", 90))
    if int(os.getenv("NO_HW_PULSE", 0)):
        options.disable_hardware_pulsing = True
    # Runtime options
    if os.getenv("SLOWDOWN_GPIO", None) != None:
        options.gpio_slowdown = int(os.getenv("SLOWDOWN_GPIO"))
    if int(os.getenv("DAEMON", 0)): 
        options.daemon = 1
    if not int(os.getenv("NO_DROP_PRIVS", 0)):
        options.drop_privileges=False
    
    # Drop priv UID/GID?

    return RGBMatrix(options = options)

def webcolor_to_rgb(color: str) -> tuple: 
    if color.startswith("#"):
        colorRgb = webcolors.hex_to_rgb(color)
    else:
        colorRgb = webcolors.name_to_rgb(color)
    return tuple(colorRgb)
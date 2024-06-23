#!/bin/python
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from dotenv import load_dotenv
import os

FONTS_PATH = "../fonts/"

def matrix_from_env():
    # Load environment vars, create options object
    load_dotenv()
    options = RGBMatrixOptions()

    options.hardware_mapping = os.getenv("GPIO_MAPPING")
    options.panel_type = os.getenv("LED_PANEL_TYPE")
    options.rows = int(os.getenv("MATRIX_ROWS"))
    options.cols = int(os.getenv("MATRIX_COLS"))
    options.chain_length = int(os.getenv("CHAIN_LENGTH"))
    options.parallel = int(os.getenv("PARALLEL"))
    options.multiplexing = int(os.getenv("MUX"))
    options.pixel_mapper_config = os.getenv("PX_MAP")
    options.pwm_bits = int(os.getenv("PWM_BITS"))
    options.scan_mode = int(os.getenv("SCAN_MODE"))
    options.row_address_type =  int(os.getenv("ADDR_TYPE"))
    options.inverse_colors = int(os.getenv("INVERT_COLORS"))
    options.led_rgb_sequence = os.getenv("RGB_SEQ")
    options.pwm_lsb_nanoseconds = int(os.getenv("PWM_LSB_NS"))
    options.pwm_dither_bits = int(os.getenv("PWM_DITHER_BITS"))
    options.show_refresh_rate = int(os.getenv("SHOW_REFRESH"))
    options.limit_refresh_rate_hz = int(os.getenv("LIMIT_REFRESH"))
    options.brightness = int(os.getenv("BRIGHTNESS"))
    if int(os.getenv("NO_HW_PULSE")):
        options.disable_hardware_pulsing = True
    # Runtime options
    if os.getenv("SLOWDOWN_GPIO", None) != None:
        options.gpio_slowdown = int(os.getenv("SLOWDOWN_GPIO"))
    if int(os.getenv("DAEMON")): 
        options.daemon = 1
    if not int(os.getenv("NO_DROP_PRIVS")):
        options.drop_privileges=False
    
    # Drop priv UID/GID?

    return RGBMatrix(options = options)

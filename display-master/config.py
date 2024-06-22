# Add RGBMatrix source code (in submodule) to system paths
# import sys
# SRC_PATH = "../rgbmatrix-src/bindings/python"
# SRC_PATH = "/home/pi/rpiDisplay/rgbmatrix-src/bindings/python"
# sys.path.insert(1, SRC_PATH)

from rgbmatrix import RGBMatrix, RGBMatrixOptions
import dotenv
import os


def matrix_from_env():
    # Load environment vars, create options object
    load_dotenv()
    options = RGBMatrixOptions()

    options.hardware_mapping = os.getenv("GPIO_MAPPING")
    options.panel_type = os.getenv("LED_PANEL_TYPE")
    options.rows = os.getenv("MATRIX_ROWS")
    options.cols = os.getenv("MATRIX_COLS")
    options.chain_length = os.getenv("CHAIN_LENGTH")
    options.parallel = os.getenv("PARALLEL")
    options.multiplexing = os.getenv("MUX")
    options.pixel_mapper_config = os.getenv("PX_MAP")
    options.pwm_bits = os.getenv("PWM_BITS")
    # Scan mode? - os.getenv("SCAN_MODE")
    options.row_address_type =  os.getenv("ADDR_TYPE")
    # Invert display? - os.getenv("INVERT_COLORS")
    options.led_rgb_sequence = os.getenv("RGB_SEQ")
    options.pwm_lsb_nanoseconds = os.getenv("PWM_LSB_NS")
    # Dithering? - os.getenv("PWM_DITHER_BITS")
    options.show_refresh_rate = os.getenv("SHOW_REFRESH")
    # Refresh limit?
    # Brightness?
    if os.getenv("NO_HW_PULSE"):
      options.disable_hardware_pulsing = True
    if os.getenv("SLOWDOWN_GPIO", None) != None:
        options.gpio_slowdown = self.args.led_slowdown_gpio
    if not os.getenv("NO_DROP_PRIVS"):
      options.drop_privileges=False
    # Daemon?
    # Drop priv UID/GID?

    return RGBMatrix(options = options)

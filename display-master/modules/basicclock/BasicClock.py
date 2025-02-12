#!/bin/python
'''
BasicClock module
Version 2.0

Module History: 
v1.0: 19 Jun 2024
- Basic functionality
v2.0: 12 Feb 2025
- Port to "class" model for module handler
'''

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import datetime as dt
import time
from config import FONTS_PATH

# Logging
import logging
log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)

# Class constants
DATE_X = 2
DATE_Y = 8
DATE_FORMAT = "%b %d, %Y"

TIME_X = 5
TIME_Y = 25
TIME_FORMAT_24 = "%H:%M:%S"
TIME_FORMAT_12 = "%I:%M %p"

MILITARY_TIME = True 
TZ_EST = dt.timezone(dt.timedelta(hours=-4), name="EST")

# Fonts
TIME_FONT_PATH = FONTS_PATH+"basic/7x13B.bdf"
DATE_FONT_PATH = FONTS_PATH+"basic/5x7.bdf"
FONT_COLOR = [255,255,255]
# Load fonts
timeFont = graphics.Font()
timeFont.LoadFont(TIME_FONT_PATH)
dateFont = graphics.Font()
dateFont.LoadFont(DATE_FONT_PATH)
fontColor = graphics.Color(*FONT_COLOR)

# Define BasicClock as class
class BasicClock: 
    # Define loop delay constant (in seconds)
    delay = 1


    def __init__(self, matrix):
        # Create cache canvas
        self.matrix = matrix
        self.nextCanvas = self.matrix.CreateFrameCanvas()
        log.debug(matrix)
        log.debug(self.matrix)

    # Continuously run on loop
    def loop(self):

        # Update clock
        self.nextCanvas.Clear()
        now = dt.datetime.now(tz=TZ_EST)
        # Draw date text, then time
        graphics.DrawText(self.nextCanvas, dateFont, DATE_X, DATE_Y, fontColor, 
                now.strftime(DATE_FORMAT))
        if MILITARY_TIME:
            graphics.DrawText(self.nextCanvas, timeFont, TIME_X, TIME_Y, fontColor, 
                now.strftime(TIME_FORMAT_24))
        else:
            graphics.DrawText(self.nextCanvas, timeFont, TIME_X-1, TIME_Y, fontColor, 
                now.strftime(TIME_FORMAT_12))
        self.nextCanvas = self.matrix.SwapOnVSync(self.nextCanvas)
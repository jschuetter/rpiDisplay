#!/bin/python
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import datetime as dt
import time

import config 
from config import FONTS_PATH

DATE_X = 2
DATE_Y = 8
DATE_FORMAT = "%b %d, %Y"
TIME_X = 5
TIME_Y = 25
TIME_FORMAT_24 = "%H:%M:%S"
TIME_FORMAT_12 = "%I:%M %p"
MILITARY_TIME = True 
TZ_EST = dt.timezone(dt.timedelta(hours=-4), name="EST")


# Load matrix from .env values
matrix = config.matrix_from_env()

# Load fonts
timeFont = graphics.Font()
timeFont.LoadFont(FONTS_PATH+"basic/7x13B.bdf")
dateFont = graphics.Font()
dateFont.LoadFont(FONTS_PATH+"basic/5x7.bdf")
fontColor = graphics.Color(255, 255, 255)

def main():
    # Create canvas for caching next frame
    nextCanvas = matrix.CreateFrameCanvas()

    # Continuously update clock
    while True:
        nextCanvas.Clear()
        now = dt.datetime.now(tz=TZ_EST)
        # Draw date text, then time
        graphics.DrawText(nextCanvas, dateFont, DATE_X, DATE_Y, fontColor, 
                now.strftime(DATE_FORMAT))
        if MILITARY_TIME:
            graphics.DrawText(nextCanvas, timeFont, TIME_X, TIME_Y, fontColor, 
                now.strftime(TIME_FORMAT_24))
        else:
            graphics.DrawText(nextCanvas, timeFont, TIME_X-1, TIME_Y, fontColor, 
                now.strftime(TIME_FORMAT_12))
        nextCanvas = matrix.SwapOnVSync(nextCanvas)
        time.sleep(1)

if __name__=="__main__":
    main()

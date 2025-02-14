#!/bin/python
"""Boilerplate code for creating new matrix layouts"""

# Import config module
import sys
sys.path.insert(0, "../..")

import config
from config import FONTS_PATH

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time
import faulthandler

# Element dependencies
from PIL import Image

# Load matrix from .env values
matrix = config.matrix_from_env()
faulthandler.enable()

font = graphics.Font()
font.LoadFont(FONTS_PATH+"basic/4x6.bdf")
print("font")
color = graphics.Color(255, 255, 255)
print("color")

def main():
    print("main")
    # Create canvas for caching next frame
    canvas = matrix.CreateFrameCanvas()
    print("canvas")
    canvas.Clear()

    # Draw elements

    # IconElement "wttr"
    #   Path: ../weather/ptlyCloudy_day.bmp
    #   Pos: [0, 0]

    # img = Image.open("../weather/ptlyCloudy_day.bmp")
    # img = img.convert("RGB")
    # canvas.SetImage(img, 0, 0)
    # print("img")

    # TextElement "date"
    #   Text: 09 Feb 2025
    #   Font: basic/4x6.bdf
    #   Color: [255, 255, 255]
    #   Pos: [20, 7]
    graphics.DrawText(canvas, font, 20, 7, color, "hello")
    print("text")
    # while True:
    #     canvas.Clear()
    #     # now = dt.datetime.now(tz=TZ_EST)
    #     # Draw date text, then time
    #     graphics.DrawText(canvas, font, 0, 0, color, 
    #             "hello")
    #     # if MILITARY_TIME:
    #     #     graphics.DrawText(nextCanvas, timeFont, TIME_X, TIME_Y, fontColor, 
    #     #         now.strftime(TIME_FORMAT_24))
    #     # else:
    #     #     graphics.DrawText(nextCanvas, timeFont, TIME_X-1, TIME_Y, fontColor, 
    #     #         now.strftime(TIME_FORMAT_12))
    #     canvas = matrix.SwapOnVSync(canvas)
    #     time.sleep(1)

    canvas = matrix.SwapOnVSync(canvas)
    print("newCanvas")

    while True: 
        time.sleep(1)


if __name__ == "__main__":
    main()
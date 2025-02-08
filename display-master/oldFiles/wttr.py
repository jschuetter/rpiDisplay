#!/bin/python
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import datetime as dt
import time
import python_weather as weather
import asyncio
from PIL import Image
import subprocess
import json

import config 
from config import FONTS_PATH

CITY_NAME = "Cincinnati"
TZ_EST = dt.timezone(dt.timedelta(hours=-4), name="EST")
CLOCK_X = 40
CLOCK_Y = 10
TIME_FORMAT = "%-I:%M"
TMP_X = 0
TMP_Y = 5

RES_PATH = "../module-resources/weather/"

# Load matrix from .env values
matrix = config.matrix_from_env()

# Load fonts
clockFont = graphics.Font()
clockFont.LoadFont(FONTS_PATH+"basic/4x6.bdf")
fontBig = graphics.Font()
fontBig.LoadFont(FONTS_PATH+"basic/6x10.bdf")
fontSmall = graphics.Font()
fontSmall.LoadFont(FONTS_PATH+"basic/4x6.bdf")
fontColor = graphics.Color(255, 255, 255)

def set_bg(canvas):
    with Image.open(BG_PATH) as img:
        img = img.convert("RGB")
        canvas.SetImage(img)
        return canvas

async def refresh(canvas):
    canvas.Clear()
    # Get & print current time
    # now = dt.datetime.now(tz=TZ_EST)
    # graphics.DrawText(canvas, clockFont, CLOCK_X, CLOCK_Y, fontColor, 
    #         now.strftime(TIME_FORMAT))
    # Get & print weather report
    jsonResult = subprocess.run(["curl","wttr.in?0QT&format=j1"], capture_output=True, text=True)
    resultDict = json.loads(jsonResult.stdout)

    # Add icon
    with Image.open(RES_PATH+"sunny.bmp") as icon:
        canvas.SetImage(icon.convert("RGB"))

    # Display weather data
    curCond = resultDict["current_condition"][0]
    graphics.DrawText(canvas, fontBig, 25, 20, fontColor, curCond["temp_F"])
    graphics.DrawText(canvas, fontSmall, 25, 30, fontColor, curCond["weatherDesc"][0]["value"])
    # yVal = TMPV_Y
    # for line in iter(result.stdout.splitlines()): 
    #     print(line)
    #     graphics.DrawText(canvas, fontSmall, TMP_X, yVal, fontColor, line)
    #     yVal += 7

    return canvas


async def main():
    # Create canvas for caching next frame
    nextCanvas = matrix.CreateFrameCanvas()

    dispTime = dt.datetime.now(tz=TZ_EST)
    await refresh(nextCanvas)
    matrix.SwapOnVSync(nextCanvas)
    while True:
        now = dt.datetime.now(tz=TZ_EST)
        if now.minute != dispTime.minute: 
            await refresh(nextCanvas)
            matrix.SwapOnVSync(nextCanvas)
            dispTime = dt.datetime.now(tz=TZ_EST)
        time.sleep(2)

if __name__=="__main__":
    asyncio.run(main())

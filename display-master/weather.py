#!/bin/python
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import datetime as dt
import time
import python_weather as weather
import asyncio
from PIL import Image

import config 
from config import FONTS_PATH

CITY_NAME = "Cincinnati"
TZ_EST = dt.timezone(dt.timedelta(hours=-4), name="EST")
CLOCK_X = 40
CLOCK_Y = 10
TIME_FORMAT = "%-I:%M"
TMP_X = 5
TMP_Y = 15

BG_PATH = "../module-resources/weather/wthr_grad_softField.bmp"

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

async def get_weather(city: str):
    async with weather.Client(unit=weather.IMPERIAL) as client: 
        localWeather = await client.get(city)
        print(localWeather.current)
        return localWeather.current

def set_bg(canvas):
    with Image.open(BG_PATH) as img:
        img = img.convert("RGB")
        canvas.SetImage(img)
        return canvas

async def refresh(canvas):
    canvas.Clear()
    set_bg(canvas)
    # Get & print current time
    now = dt.datetime.now(tz=TZ_EST)
    graphics.DrawText(canvas, clockFont, CLOCK_X, CLOCK_Y, fontColor, 
            now.strftime(TIME_FORMAT))
    # Get & print weather report
    cond = await get_weather(CITY_NAME)
    xPos = graphics.DrawText(canvas, fontBig, TMP_X, TMP_Y, fontColor, (str(cond.temperature)+"\N{DEGREE SIGN}"))

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
        time.sleep(2)

if __name__=="__main__":
    asyncio.run(main())

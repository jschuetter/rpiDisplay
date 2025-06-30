#!/bin/python
'''
Weather Module
Version 0.1
Jacob Schuetter

Module history:
Version 0.1: 29 Jun 2025
'''

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config
from modules.Module import Module
from Components import *
import requests, json
from datetime import datetime as dt
import constants
import time

# Logging
import logging
log = logging.getLogger(__name__)

# Element dependencies
# IconElement
from PIL import Image, ImageDraw
# TextElement
import webcolors
from pathlib import Path

# ImageElement 'icon'
#   Path: display-master/modules/weather/assets/sun.png
#   Pos: [1, 2]
#   Size: 18

# TextElement 'precip'
#   Text: /20%
#   Font: fonts/uushi/uushi.bdf
#   Color: #ffffff
#   Pos: [38, 20]

# TextElement 'details'
#   Text: 63°
#   Font: fonts/sq/sqb.bdf
#   Color: #ffffff
#   Pos: [20, 20]

# TextElement 'conditions'
#   Text: Sunny
#   Font: fonts/basic/5x8.bdf
#   Color: #ffffff
#   Pos: [21, 7]

# TextElement 'location'
#   Text: Cincinnati
#   Font: fonts/basic/5x7.bdf
#   Color: #ffffff
#   Pos: [1, 31]

class Weather(Module):
    '''
    Simple weather display based on wttr.in.

    See https://wttr.in/:help and 
    https://github.com/chubin/wttr.in for API documentation.
    '''

    ASSETS_PATH = "display-master/modules/weather/assets/"
    API_BASE_URL = "https://wttr.in/"
    ICON_LIB = constants.GLASSMORPHISM_ICON_MAP

    def __init__(self, matrix, canvas, location=""):
        '''
        Parameters
        -----------
        location: str [optional]
            Location for weather data, as city name, 
            postal code, airport code, or GPS coords.
            (e.g. "Cincinnati", "45202", "cvg", "39.1031,-84.5120")
        '''
        # Init module with delay of 15 minutes
        super().__init__(matrix, canvas, delay=5)
        # Declare dynamic values
        self.data = {
            "conditions": "",
            "conditionCode": 0,
            "temperature": "",
            "precip_chance": "",
            "moonphase": "",
            "sunrise": "",
            "sunset": "",
        }
        self.update_error = False

        # Module settings
        self.location_name = location
        self.locale = location.replace(" ", "+") # Location setting for weather API (spaces replaced with '+')
        self.fahrenheit = True      # Default to Fahrenheit
        self.use_feelslike = False  # Use 'feels like' temperature
        self.query_params = {
            "format": "j1",  # JSON format
            "lang": "en",    # Language
        }

        # Icon background - icon added later by compositing
        self.ICON_SIZE = 18         # Size of the icon  
        self.icon_bg = Image.new(
            "RGBA", 
            (self.ICON_SIZE, self.ICON_SIZE), 
            (0, 0, 0, 255)
        )
        self.icon = self.icon_bg    # Initialize icon object to blank

        self.components = [
            PILImage(0, 0, self.icon),
            Text(1, 31, self.location_name, font="basic/5x7.bdf"),       # Location text
            Text(21, 7, self.data["conditions"], font="basic/5x8.bdf"),          # Conditions text
            Text(20, 20, self.data["temperature"], font="sq/sqb.bdf"),           # Temperature text
            Text(38, 20, self.data["precip_chance"], font="uushi/uushi.bdf"),    # Precipitation chance text
        ]
        
    # Initial frame draw
    def draw(self):
        self.update()
        super().draw()

    def update(self): 
        '''Call wttr.in API and draw module background'''
        # Get data from wttr.in
        log.info("Fetching weather data...")
        response = requests.get(self.API_BASE_URL + self.locale, params=self.query_params)
        if response.status_code == 200:
            log.info("Successfully retrieved weather data.")
            data = response.json()

            # Parse weather data & format for display
            # self.location_name = data['nearest_area'][0]['areaName'][0]['value']
            self.data["conditions"] = data["current_condition"][0]["weatherDesc"][0]["value"]
            self.data["conditionCode"] = int(data["current_condition"][0]["weatherCode"])
            if not self.use_feelslike: 
                self.data["temperature"] = f"{data['current_condition'][0]['temp_F']}°" if self.fahrenheit else f"{data['current_condition'][0]['temp_C']}°"
            else: 
                self.data["temperature"] = f"{data['current_condition'][0]['FeelsLikeF']}°" if self.fahrenheit else f"{data['current_condition'][0]['FeelsLikeC']}°"

            # Get precipitation chance for next 3-hour block today
            today_idx = 0
            next_hour_idx = (dt.now().hour // 3) + 1
            if next_hour_idx > 7: 
                # If in last hour block, wrap to tomorrow's forecast
                next_hour_idx = 0
                today_idx = 1
            self.data["precip_chance"] = f"{data['weather'][today_idx]['hourly'][next_hour_idx]['chanceofrain']}%"

            # Astronomical data
            self.data["moonphase"] = data["weather"][today_idx]["astronomy"][0]["moon_phase"]
            self.data["sunrise"] = data["weather"][today_idx]["astronomy"][0]["sunrise"]
            self.data["sunset"] = data["weather"][today_idx]["astronomy"][0]["sunset"]
            
            self.update_error = False
        else:
            log.error(f"Failed to fetch weather data: {response.status_code}")
            self.update_error = True

        # Get icon, add background
        dayNight = "night"
        if (
            dt.now() < dt.strptime(self.data["sunrise"], "%I:%M %p") 
            or dt.now() > dt.strptime(self.data["sunset"], "%I:%M %p")
        ):
            dayNight = "day"
        
        # Declare icon object in function scope
        try: 
            iconPath = self.ASSETS_PATH + self.ICON_LIB["dir_name"] + self.ICON_LIB[dayNight][self.data["conditionCode"]]
            iconTemp = Image.open(iconPath).convert("RGBA")
        except KeyError: 
            # Use Partly Cloudy code as default if icon not found in mapping
            log.info("Used default icon for weather code.")
            iconPath = self.ASSETS_PATH + self.ICON_LIB["dir_name"] + self.ICON_LIB[dayNight][116]
            iconTemp = Image.open(iconPath)
        # Resize image
        iconTemp.thumbnail((self.ICON_SIZE, self.ICON_SIZE), Image.Resampling.LANCZOS)
        blackBg = Image.new("RGBA", iconTemp.size, (0, 0, 0, 255))
        # iconTemp = iconTemp.convert("RGBA")
        self.icon = Image.alpha_composite(blackBg, iconTemp)
        self.icon = self.icon.convert("RGB")  # Convert to RGB for compatibility with RGBMatrix

        self.components = [
            PILImage(0, 0, self.icon),
            Text(1, 31, self.location_name, font="basic/5x7.bdf"),       # Location text
            Text(21, 7, self.data["conditions"], font="basic/5x8.bdf"),          # Conditions text
            Text(20, 20, self.data["temperature"], font="sq/sqb.bdf"),           # Temperature text
            Text(38, 20, self.data["precip_chance"], font="uushi/uushi.bdf"),    # Precipitation chance text
        ]
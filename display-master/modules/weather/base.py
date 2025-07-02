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
from PIL import Image, ImageDraw, ImageEnhance
# TextElement
import webcolors
from pathlib import Path

class Weather(Module):
    '''
    Simple weather display based on wttr.in.

    See https://wttr.in/:help and 
    https://github.com/chubin/wttr.in for API documentation.
    '''

    ASSETS_PATH = "display-master/modules/weather/assets/"
    API_BASE_URL = "https://wttr.in/"
    ICON_LIB = constants.GLASSMORPHISM_ICON_MAP
    # ICON_LIB = constants.MINIMALIST_ICON_MAP
    BRIGHTEN_ICON = True
    BRIGHTEN_FACTOR = 3
    ICON_SIZE = 18  # Size of the icon
    BACKGROUND_COLOR = (0,32,64)

    def set_components(self): 
        detailTextHeight = 6 + self.icon.height // 2
        self.components = [
            PILImage(2, 8, self.icon),
            Text(1, 31, self.location_name, font="basic/5x7.bdf"),       # Location text
            Text(1, 7, self.data["conditions"], font="basic/5x8.bdf"),          # Conditions text
            Text(self.ICON_SIZE + 3, 8 + detailTextHeight, self.data["temperature"], font="sq/sqb.bdf"),           # Temperature text
            Text(self.ICON_SIZE + 22, 8 + detailTextHeight + 1, self.data["precip_chance"], font="uushi/uushi.bdf"),    # Precipitation chance text
        ]
        if self.bg: 
            # If background color is not black, add background component first in stack
            self.components.insert(0, PILImage(0, 0, self.bg))

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
            "conditionCode": 0,
            "conditions": "",
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

        self.icon = Image.new("RGB", (self.ICON_SIZE, self.ICON_SIZE), self.BACKGROUND_COLOR)    # Initialize icon object to blank
        if self.BACKGROUND_COLOR != (0, 0, 0): 
            # If background color is not black, add background component
            self.bg = Image.new("RGB", (self.matrix.width, self.matrix.height), self.BACKGROUND_COLOR)
        else: 
            self.bg = None

        self.set_components()
        
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
            self.data["conditionCode"] = int(data["current_condition"][0]["weatherCode"])
            self.data["conditions"] = constants.WWO_CODE[self.data["conditionCode"]]
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
            self.data["precip_chance"] = f"/{data['weather'][today_idx]['hourly'][next_hour_idx]['chanceofrain']}%"

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
        if self.BRIGHTEN_ICON:
            # Brighten icon if enabled
            enhancer = ImageEnhance.Brightness(iconTemp)
            iconTemp = enhancer.enhance(self.BRIGHTEN_FACTOR)
        blackBg = Image.new("RGBA", iconTemp.size, (*self.BACKGROUND_COLOR, 255))
        # iconTemp = iconTemp.convert("RGBA")
        self.icon = Image.alpha_composite(blackBg, iconTemp)
        self.icon = self.icon.convert("RGB")  # Convert to RGB for compatibility with RGBMatrix

        # Update components
        self.set_components()
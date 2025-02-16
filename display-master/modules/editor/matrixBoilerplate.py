#!/bin/python
'''
Boilerplate code for creating new matrix values
'''

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config

# Logging
import logging
log = logging.getLogger(__name__)

# Element dependencies
# IconElement
from PIL import Image
# TextElement
import webcolors
from pathlib import Path


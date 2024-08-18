#!/bin/python
'''Boilerplate code for creating new matrix layouts'''

# Import config module
import sys
sys.path.insert(0, "../..")

import config
from config import FONTS_PATH

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Element dependencies
from PIL import Image

# Load matrix from .env values
matrix = config.matrix_from_env()

def main():
    # Create canvas for caching next frame
    canvas = matrix.CreateFrameCanvas()

    # Draw elements


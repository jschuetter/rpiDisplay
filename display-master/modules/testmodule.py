#!/bin/python
'''
TestModule
Version 1.0

Module History: 
v1.0: 22 May 2025
- Exists solely for testing new features
'''

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from config import FONTS_PATH
# import Components
from Components import *

# Logging
import logging
log = logging.getLogger(__name__)

class TestModule: 
    # Define loop delay constant (in seconds)
    delay = 1
    doloop = 0

    def __init__(self, matrix):
        # Create cache canvas
        self.matrix = matrix
        self.nextCanvas = self.matrix.CreateFrameCanvas()
        self.components = [
            # Add components here!
            Rect(0, 0, 20, 10, (0, 0, 255), (255, 0, 0), 1)
        ]

    def draw(self):
        self.nextCanvas.Clear()
        for c in self.components: 
            c.draw(self.nextCanvas)
        self.matrix.SwapOnVSync(self.nextCanvas)

    def loop(self):
        self.nextCanvas.Clear()
        for c in self.components: 
            c.loop()
        self.matrix.SwapOnVSync(self.nextCanvas)
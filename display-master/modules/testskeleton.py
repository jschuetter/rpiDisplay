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
from modules.Module import Module

# Logging
import logging
log = logging.getLogger(__name__)

class TestModule(Module): 

    def __init__(self, matrix, canvas):
        super().__init__(matrix, canvas, doLoop=False, delay=1)
        self.components = [
            # Add components here!
        ]

    def draw(self):
        self.canvas.Clear()
        for c in self.components: 
            c.draw(self.canvas)
        self.matrix.SwapOnVSync(self.canvas)

    def loop(self):
        self.canvas.Clear()
        for c in self.components: 
            c.loop()
        self.matrix.SwapOnVSync(self.canvas)
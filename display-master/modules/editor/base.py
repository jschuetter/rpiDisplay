#!/bin/python
'''
Editor Module
Version 0.2
Jacob Schuetter

Module history: 
v0.1: 12 Feb 2025
v0.2: 15 Feb 2025
- Moved cmdloop() call to draw() method (for consistency across modules)
'''

# RGB Matrix dependencies
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config 
from config import FONTS_PATH

# CLI dependencies
import cmd
# from modules.src import Elements
import Elements
from ElementEditor import ElementEditor
from ModuleEditor import ModuleEditor
import cli # Relevant global vars & methods
# from cli import parse, \
    # refresh_canvas, write_json, print_props, update_all

import os, re, json
import logging
from typing import Any
from warnings import warn
from shutil import copy as fcopy
from copy import deepcopy

# Logger
# N.B. logger used only for system logs. CLI messages made using `print`
import logging
log = logging.getLogger(__name__)

class Editor: 
    doloop = 0
    delay = 1

    def __init__(self, matrix): 
        self.matrix = matrix
        self.canvas = self.matrix.CreateFrameCanvas()
        self.medit = ModuleEditor(self.matrix, self.canvas)
        self.doloop = 0

    def draw(self):
        self.medit.cmdloop()

    def loop(self): 
        # Define loop method by convention; this one does nothing
        return
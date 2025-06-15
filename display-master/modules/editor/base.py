#!/bin/python
'''
Editor Module
Version 1.1
Jacob Schuetter

Module history: 
v0.1: 12 Feb 2025
v0.2: 15 Feb 2025
- Moved cmdloop() call to draw() method (for consistency across modules)
v1.0: 20 May 2025
- First fully-functioning version with basic Element types
v1.1: 14 Jun 2025
- Misc. QOL improvements
- Added inheritance from Module class
'''

# RGB Matrix dependencies
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config 
from config import FONTS_PATH

# CLI dependencies
import cmd
from modules.Module import Module
import Elements
from ElementEditor import ElementEditor
from ModuleEditor import ModuleEditor

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

class Editor(Module):

    def __init__(self, matrix, canvas): 
        '''
        Additional Parameters
        ----------------------
        medit: ModuleEditor
            Custom CLI based on Python cmd module used to lay out modules
        '''
        super().__init__(matrix, canvas)
        self.medit = ModuleEditor(self.matrix, self.canvas)

    def draw(self):
        self.medit.cmdloop()
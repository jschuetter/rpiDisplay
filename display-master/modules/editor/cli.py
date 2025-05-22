#!/bin/python
'''
cli.py
Helper code & methods for Editor module

Last updated: 16 Feb 2025
Jacob Schuetter
'''

# RGB self.matrix dependencies
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config 
from config import FONTS_PATH, EXPORT_PATH

import os
from warnings import warn
import json
from typing import Any
from shutil import copy as fcopy

from modules.src import Elements

import logging
log = logging.getLogger(__name__)

ELEMENT_TYPES = {"icon": Elements.IconElement, 
        "image":Elements.ImageElement, 
        "text": Elements.TextElement, 
        "rect":Elements.RectElement, 
        "ellipse":Elements.EllipseElement,
        "line":Elements.LineElement,
        "circle":Elements.CircleElement
        }
ELEMENT_CLASS_NAMES = { class_:name_ for name_, class_ in ELEMENT_TYPES.items()}

# Provide definitions for common helper functions (those not dealing with display/element operations)
#   outside class definition (also provided inside for consistency)
def parse(line: str) -> tuple:
    'Convert space-delimited arguments to tuple of strings'
    argsList = line.split()

    # Quotation checking
    needCloseQuote = False
    listLen = len(argsList)
    i=0
    while i < listLen:
        # Check for starting quotations
        if argsList[i].startswith("\""):
            needCloseQuote = True
            # Remove quotation mark
            argsList[i] = argsList[i][1:]
            for j in range(i, len(argsList)):
                # Check for end quotations
                if argsList[j].endswith("\""):
                    for k in range(i+1,j+1):
                        argsList[i] += f" {argsList[i+1]}"
                        del argsList[i+1]
                    needCloseQuote = False
                    # Remove quotation mark
                    argsList[i] = argsList[i][:-1]
                    listLen = len(argsList)
                    break
        i += 1

    if needCloseQuote: 
        print ("ERROR: no close quotation found")
        return tuple()

    args = tuple(argsList)
    log.debug(args)
    return args

def print_props(obj: Any):
    '''Print all object properties and their values in formatted output
    
    obj: Any
        Object to print'''
    
    for k, v in vars(obj).items():
        if isinstance(v, Elements.Property):
            print(f"{k}: {v.value}")
        else: 
            print(f"{k}: {v}")


# Export method
# Define boilerplate code to follow class header in exported modules
CLASS_BOILERPLATE_1 = """
    # Define loop delay constant (in seconds)
    doloop = config.DEF_DOLOOP
    delay = config.DEF_DELAY

    def __init__(self, matrix):
        # Create cache canvas
        self.matrix = matrix
        self.canvas = self.matrix.CreateFrameCanvas()
        log.debug(matrix)
        log.debug(self.matrix)

    # Initial frame draw
    def draw(self):
        self.canvas.Clear()
        # Element code here
"""
CLASS_BOILERPLATE_2 = """
    # Code to refresh on every frame update
    def loop(self): 
        self.canvas.Clear()
        # Element code here
"""
# Number of tabs to insert before each line of element code
TAB_LVL = "\t\t"

def export_code(fileName: str, compElements: list):
    '''Exports current composition as Python code and writes to output file.
    N.B. all code used for exporting must use 4-space tabs (not 2-space or tab chars).
    
    fileName: name of new file to be created (no extension)
        Must only be composed of alphanumeric chars and underscores
        (Same convention as composition names)
    compElements: list of elements in composition to be exported 
        (will usually be working["elements"])'''

    BOILERPLATE_PATH = "display-master/modules/editor/matrixBoilerplate.py"
    exportPath = f"{EXPORT_PATH}{fileName}.py"

    fcopy(BOILERPLATE_PATH, exportPath)
    # Copy boilerplate file and append element code
    with open(exportPath, 'a') as codeFile: 
        # Write init code
        for el in compElements: 
            codeFile.write(el.init_code() + "\n")
        codeFile.write("\n\n")
        # Write class header
        codeFile.write(f"class {fileName.capitalize()}:\n")
        # Write class boilerplate
        codeFile.write(CLASS_BOILERPLATE_1)
        # Write draw method
        for el in compElements: 
            codeFile.write(el.draw_code() + "\n")
        codeFile.write("        self.matrix.SwapOnVSync(self.canvas)\n")
        # Write loop method
        codeFile.write(CLASS_BOILERPLATE_2)
        for el in compElements: 
            codeFile.write(el.loop_code() + "\n")
        codeFile.write("        self.matrix.SwapOnVSync(self.canvas)\n")

        
    # Update file permissions -- add write permission to group
    os.chmod(exportPath, 0o664)
    print(f"Exported comp {fileName} as {fileName}.py")
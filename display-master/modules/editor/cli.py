#!/bin/python
# Insert project root directory into sys.path
import sys
sys.path.insert(0, "../..")

# RGB Matrix dependencies
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config 
from config import FONTS_PATH

import logging
from warnings import warn
import json
from typing import Any

from modules.src import Elements

log = logging.getLogger(__name__)

# Standard path to store JSON files at
SRC_PATH = "./srcFiles"
# Global variable containing current working data (read in from JSON or created from CLI)
# Contains comp name, comp json path, list of Element objects, dict of Element names & data
working = {}
matrix = config.matrix_from_env()
canvas = matrix.CreateFrameCanvas()

ELEMENT_TYPES = {"icon": Elements.IconElement, 
        "image":None, 
        "text":None, 
        "rect":None, 
        "ellipse":None
        }
ELEMENT_CLASS_NAMES = { class_:name_ for name_, class_ in ELEMENT_TYPES.items()}
def parse(line: str) -> tuple:
    'Convert space-delimited arguments to tuple of strings'
    args = tuple(line.split())
    log.debug(args)
    return args

def new_json():
    '''Generates fresh JSON template

    Creates sub-dict for each class name in ELEMENT_TYPES
    '''
    outDict = {}
    for t in ELEMENT_TYPES:
        outDict[t] = {}
    return outDict

def write_json():
    'Write changes to JSON file'
    global working
    # Generate JSON from element list
    if not working: 
        warn("No open composition, no JSON written", RuntimeWarning)
        return
    workingJson = {}
    for el in working["elements"]:
        elType = ELEMENT_CLASS_NAMES[type(el)]
        if workingJson.get(elType) is None:
            workingJson[elType] = []
        workingJson[elType].append(vars(el))

    with open(working["path"], "w") as file:
        json.dump(workingJson, file, cls=Elements.CEnc)

def print_props(obj: Any):
    '''Print all object properties and their values in formatted output
    
    obj: Any
        Object to print'''
    
    for k, v in vars(obj).items():
        if isinstance(v, Elements.Property):
            print(f"{k}: {v.value}")
        else: 
            print(f"{k}: {v}")

def refresh_canvas():
    global working, canvas, matrix
    if not working:
        raise RuntimeError("Cannot draw without open composition")

    canvas = matrix.CreateFrameCanvas()
    for el in working["elements"]:
        el.draw(canvas)
    matrix.SwapOnVSync(canvas)
    return

def sort_working():
    '''Sort working dictionary by layer, then re-index element layers based on new positions'''
    working["elements"].sort(key=lambda el: el.layer.value)
    for i in range(len(working["elements"])):
        el = working["elements"][i]
        el.layer.value = i



def update_all(do_sort: bool = True, do_reindex: bool = True, do_write_json: bool = True, do_refresh_canvas: bool = True):
    '''Sort working dictionary by layer, then update JSON file and matrix display
    
    do_sort: runs sort_working() if true
    do_write_json: runs write_json() if true
    do_refresh_canvas: runs refresh_canvas() if true'''

    # if do_sort: sort_working()
    if do_sort: working["elements"].sort(key=lambda el: el.layer.value)
    if do_reindex: 
        for i in range(len(working["elements"])):
            el = working["elements"][i]
            el.layer.value = i
    if do_write_json: write_json()
    if do_refresh_canvas: refresh_canvas()
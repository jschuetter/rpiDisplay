#!/bin/python
# Import config module
# import sys
# sys.path.insert(0, "../..") # For config module
# sys.path.insert(1, "../src") # For modules in this folder

# import config
# from config import FONTS_PATH

# from copy import deepcopy
# from typing import Any, NewType
import os, json, webcolors

# from rgbmatrix import FrameCanvas, graphics

def add_param(name: str, type_: type, desc: str, optional: bool = False) -> dict:
    '''Helper method for creating parameter dictionaries more concisely
    
    Returns dict containing param data'''
    return {
        "name": name,
        "type": type_,
        "description": desc, 
        "optional": optional
    }
def print_params(params):
    paramDocs = ""
    for p in params:
        paramDocs += f"{p.get('name')}: {p.get('type')}\n\t{p.get('description')}\n\t" + \
            f"Optional: {p.get('optional')}\n"
    return paramDocs

class CEnc(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

        
def colorFormat(obj) -> list: 
    if type(obj.color.value) is list: 
        return obj.color.value

    try:
        if obj.color.value.startswith("#"):
            colorRgb = webcolors.hex_to_rgb(obj.color.value)
        else:
            colorRgb = webcolors.name_to_rgb(obj.color.value)
    except ValueError as e:
        print(e)
        print("Color defaulted to white.")
        obj.color.value = "white"
        colorRgb = webcolors.name_to_rgb(obj.color.value)
    
    return list(colorRgb)
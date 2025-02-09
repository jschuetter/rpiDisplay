#!/bin/python

# Import config module
# import sys
# sys.path.insert(0, "../..")

# import config
# from config import FONTS_PATH

# from copy import deepcopy
from typing import Any, NewType
# import os, json

# from rgbmatrix import FrameCanvas, graphics

class Property:
    '''Custom class for MatrixElement properties

    Allows adding use data along with each variable
    - Allowed Property modes: 
        - l (literal): assignable by literal value only
        - s (scrollable): can scroll through list of allowed values in editor
        - n (numeric): can use arrow keys to increment/decrement values
        - n2 (numeric tuple): can use arrow keys (left/right, up/down) to 
            increment/decrement each tuple value respectively
    '''

    allowedModes = ["l", "s", "n", "n2"]
    modemap = {
        "l":"literal",
        "s":"scrollable",
        "n":"numeric",
        "n2":"numeric tuple"
    }
    modehints = {
        "l":"assignable by literal value only",
        "s":"scroll through allowed values using up/down arrows",
        "n":"numeric value; can be incremented/decremented using up/down arrows",
        "n2":"tuple of numeric values; can be adjusted using (left/right, up/down) arrow keys"
    }
    typemap_str = {
        "str":str,
        "int":int,
        "None":None
    }
    typemap_cls = {
        str:"str",
        int:"int",
        None:"None"
    }
    
    @classmethod
    def from_dict(cls, src: dict):
        clsObj = cls("default", None)
        for k, v in src.items():
            if type(v) is dict:
                setattr(clsObj, k, Property.from_dict(v))
            else: 
                setattr(clsObj, k, v)
        return clsObj
    
    def __init__(self, val: Any, typ: type, mod: str = "l", opt: list = []):
        '''
        Parameters
        ----------
        val: Any
            Value of parameter
        typ: type
            Type of parameter
        mod: str
            parameter mode (see class docstring)
        _opt: list[str]
            list of available value options
            Required for "scrollable" mode
        '''

        if mod not in self.allowedModes: 
            raise ValueError("Invalid mode string")
        self.mode = mod
        if self.mode == "s" and opt == []:
            raise ValueError("Options list is required for scrollable mode.")
        self.options = opt
        if self.options and val not in self.options:
            print(f"Allowed list: {self.options}")
            raise ValueError("Provided value not in allowed list.")
        self.value = val
        # if typ not in Property.typemap_cls:
        #     raise ValueError("Type not in class typemap")
        # Convert type to tuple (for easier checking)
        if type(typ) in [tuple, list]:
            typeTup = tuple([Property.typemap_cls[t] for t in typ])
        else:
            typeTup = (Property.typemap_cls[typ],)
        # print(self.value)
        # print(typeTup)
        self.type_ = typeTup

    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return (f"{{'value':{self.value},'type_':{self.type_},'mode':{self.mode},"
                f"'options':{self.options}}}")

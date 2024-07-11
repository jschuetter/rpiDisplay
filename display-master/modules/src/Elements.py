#!/bin/python
from rgbmatrix import FrameCanvas
from copy import deepcopy
from typing import Any, NewType
from PIL import Image
import os, json

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
    def __init__(self, _value: Any, _mode: str = "l", _opt: list = []):
        '''
        Parameters
        ----------
        _value: Any
            Value of parameter
        _mode: str
            parameter mode (see class docstring)
        _opt: list[str]
            list of available value options
            Required for "scrollable" mode
        '''

        self.value = _value
        if _mode not in self.allowedModes: 
            raise ValueError("Invalid mode string")
        self.mode = _mode
        if self.mode == "s" and _opt == []:
            raise ValueError("Options list is required for scrollable mode.")
        self.options = _opt

    def __repr__(self):
        return f"Property({self.value}, {self.mode}, {self.options})"

class MatrixElement: 
    params = [add_param("name", str, "Name of Element object (dev only).")]

    def __init__(self, _name: str):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        '''

        self.name = _name
        self.group = []
        self.pos = Property((0,0), "n2")
    
    def duplicate(self):
        return deepcopy(self)

# Element for displaying static bitmap images
# Requires .bmp filetype
class IconElement(MatrixElement):
    params = MatrixElement.params + [
        add_param("path", str, "Relative path to the default icon for this object. " +
                  "Icon must be in .bmp format."),
        add_param("x_pos", int, "X-coordinate of icon (top-left)."),
        add_param("y_pos", int, "Y-coordinate of icon (top-left)")
    ]
    docstr = "An icon in .bmp image format.\n\n" + \
        "Usage: add icon [name] [path] [x_pos] [y_pos]\n\n" + \
            print_params(params)
    
    @classmethod
    def testArgs(cls, *args) -> int:
        '''Tests validity of arguments. 
        Returns string response if invalid args. 
        Returns None if valid.'''
        if len(args) < len(cls.params): 
            return "Incorrect number of args."
        if type(args[0]) is not str: 
            return "Invalid element name."
        if not os.path.isfile(args[1]): 
            return "Invalid image path."
        elif not args[1].endswith(".bmp"):
            return "Image type must be .bmp (use Image class for pixel types)."
        for e in args[2:4]:
            try:
                int(e)
            except ValueError: 
                return "Position arguments must be int values"
        # Return None if all arguments are valid
        return None

    def __init__(self, _name: str, imgPath: str = "", x: str = "0", y: str = "0"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        imgPath: str
            Path of .bmp file to show
        _pos: tuple[int, int]
            Tuple (x,y) of position to display image (coordinate of top-left of image)
        '''

        super().__init__(_name)
        self.path = imgPath
        self.pos = Property((int(x),int(y)), "n2")
        # self.x = int(x)
        # self.y = int(y)

    def draw(self, canvas: FrameCanvas):
        img = Image.open(self.path)
        img = img.convert("RGB")
        print(self.pos.value)
        canvas.SetImage(img, self.pos.value[0], self.pos.value[1])

    def json(self):
        return self.__dict__
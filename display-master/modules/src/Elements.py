#!/bin/python
'''
Elements.py
Definition of Element class
'''

# Import config module
import config
from config import FONTS_PATH

import logging
log = logging.getLogger(__name__)

from copy import deepcopy
from typing import Any, NewType
import os, json

from rgbmatrix import FrameCanvas, graphics

from Property import Property
from Param import Parameter
from elementhelpers import *

# Element dependencies
# IconElement
from PIL import Image
# TextElement
import webcolors
from pathlib import Path

# Tab levels for export strings
METHOD_TAB = "        " # 2 levels
INIT_TAB = "" # No indent

# Base class
class MatrixElement: 
    '''Parent class for all matrix elements

    SCHEMA
    Class variables: 
    - params [list]: list of params added using the `Parameter` method
    - docstr [str]: class docstring
    Instance variables: 
    - Name [Property]: literal property containing name of element
    - Group [list]: list of strings containing names of groups of which this element is a member
    - Layer [Property]: numeric property indicating z-index of element
    - Pos [Property]: numeric pair property representing pixel coordinates of element
    [Subclasses may add data elements as needed]

    Class methods: 
    - testargs(*args) [str | None]: tests the provided tuple of arguments for
        validity according to class spec and returns str msg, or None if all are valid.
    - from_dict(dict) [MatrixElement]: constructs a MatrixElement from the provided __dict__
    Methods: 
    - __init__ [None]
    - duplicate [MatrixElement]: returns a deep copy of the element
    - draw(canvas) [None]: draws the element on the provided Canvas object
    - loop(canvas) [None]: draws the element's coded next-frame on the provided Canvas object
        Defaults to draw method
    - init_code() [str]: returns Python code for instantiating variables used by this element
    - draw_code() [str]: returns Python code for drawing the element
    - loop_code() [str]: returns of Python code for updating/maintaining element on every frame refresh
        Defaults to return same as draw_code()
    - json [dict]: returns element data as dict
    [Subclasses may also add methods if needed]
    '''

    params = [Parameter("name", str, "Name of Element object (dev only).")]
    docstr = "An element for use with an RGB LED matrix."

    @classmethod
    def testArgs(cls, *args):
        '''Tests validity of arguments. 
        Returns string response if invalid args. 
        Returns None if valid.'''
        if len(args) < len(cls.params): 
            return "Incorrect number of args."
        if type(args[0]) is not str: 
            return "Invalid element name."
        for e in args[1:3]:
            try:
                int(e)
            except ValueError: 
                return "Position arguments must be int values"
        # Return None if all arguments are valid
        return None
    
    @classmethod
    def from_dict(cls, src: dict):
        clsObj = cls("default")
        for k, v in src.items():
            if type(v) is dict:
                setattr(clsObj, k, Property.from_dict(v))
            else: 
                setattr(clsObj, k, v)
        return clsObj
    
    def __init__(self, name_: str):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        '''

        self.name = Property(name_, str)
        self.group = []
        self.layer = Property(0, int, "n")
        self.pos = Property([0,0], (int, int), "n2")
    
    def duplicate(self):
        return deepcopy(self)

    def draw(self, canvas: FrameCanvas):
        return None
    
    def loop(self, canvas: FrameCanvas):
        return self.draw(canvas)
    
    def init_code(self) -> str: 
        return "" 

    def draw_code(self) -> str:
        return "pass"
    
    def loop_code(self) -> str:
        return self.draw_code()

    def json(self) -> dict:
        return self.__dict__

#region imageElements

class IconElement(MatrixElement):
    '''Element for displaying static bitmap images
    Requires .bmp filetype'''

    params = MatrixElement.params + [
        Parameter("path", str, "Relative path to the default icon for this object. " +
                  "Icon must be in .bmp format."),
        Parameter("x_pos", int, "X-coordinate of icon (top-left)."),
        Parameter("y_pos", int, "Y-coordinate of icon (top-left)")
    ]
    docstr = "An icon in .bmp image format.\n\n" + \
        "Usage: add icon [name] [path] [x_pos] [y_pos]\n\n" + \
            print_params(params)
    
    @classmethod
    def testArgs(cls, *args):
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
    
    # @classmethod
    # def from_dict(cls, src: dict):
    #     clsObj = cls("default")
    #     for k, v in src.items():
    #         if type(v) is dict:
    #             setattr(clsObj, k, Property.from_dict(v))
    #         else: 
    #             setattr(clsObj, k, v)
    #     return clsObj

    def __init__(self, _name: str, imgPath: str = "", x: str = "0", y: str = "0"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        imgPath: str
            Path of .bmp file to show
        x: int
            X-coordinate of top-left of image)
        y: int
            Y-coordinate of top-left of image)
        '''

        super().__init__(_name)
        self.path = Property(imgPath, str)
        self.pos = Property([int(x),int(y)], (int, int), "n2")

        # Define init variable name
        self._imgVarName = f"img_{self.name.value}"
        
    def draw(self, canvas: FrameCanvas):
        img = Image.open(self.path.value)
        img = img.convert("RGB")
        canvas.SetImage(img, self.pos.value[0], self.pos.value[1])

    def init_code(self) -> str:
        imgVarname = f"img_{self.name.value}"
        return (f"{INIT_TAB}# IconElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Path: {self.path.value}\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}img_{self.name.value} = Image.open('{self.path.value}').convert('RGB')\n")
                # f"{INIT_TAB}img_{self.name.value} = img.convert('RGB')\n")
    
    def draw_code(self) -> str:
        return (
                f"{METHOD_TAB}self.canvas.SetImage(img_{self.name.value}, {self.pos.value[0]}, {self.pos.value[1]})\n")

    def json(self):
        return self.__dict__

#endregion

#region textElements

class TextElement(MatrixElement):
    '''Element for displaying static text
    Element size is determined by font and text content'''

    params = MatrixElement.params + [
        Parameter("text", str, "Text contents of element"),
        Parameter("font", str, f"Font file to use, relative to base fonts path. \
                  Fonts may be found at '{FONTS_PATH}'"),
        Parameter("textColor", str, "Hex value of font color to use (preceded by #). \
            Web color names may also be used. "),
        Parameter("x_pos", int, "X-coordinate of icon (top-left)"),
        Parameter("y_pos", int, "Y-coordinate of icon (top-left)")
    ]
    docstr = "Static text.\n\n" + \
        "Usage: add text [name] [textContent] [font] [textColor] [x_pos] [y_pos]\n\n" + \
            print_params(params)
    
    @classmethod
    def testArgs(cls, *args):
        '''Tests validity of arguments. 
        Returns string response if invalid args. 
        Returns None if valid.'''
        if len(args) < len(cls.params): 
            return "Incorrect number of args."
        if not isinstance(args[0], str):
            return "Invalid element name."
        if not isinstance(args[1], str):
            return "Text content must be str."
        fontPath = FONTS_PATH + args[2]
        if not os.path.isfile(fontPath) or not fontPath.endswith(".bdf"): 
            print(fontPath)
            return "Invalid font path."
        if args[3].startswith("#"):
            try: 
                webcolors.hex_to_rgb(args[3])
            except ValueError:
                return "Provided hex color is invalid."
        else: 
            try: 
                webcolors.name_to_rgb(args[3])
            except ValueError: 
                return "Color value must be in hex, beginning with #, or \
                a valid CSS3 color name. "
        for e in args[4:6]:
            try:
                int(e)
            except ValueError: 
                return "Position arguments must be int values"
        # Return None if all arguments are valid
        return None
    
    # @classmethod
    # def from_dict(cls, src: dict):
    #     clsObj = cls("default")
    #     for k, v in src.items():
    #         if type(v) is dict:
    #             setattr(clsObj, k, Property.from_dict(v))
    #         else: 
    #             setattr(clsObj, k, v)
    #     return clsObj

    default_font = "basic/4x6.bdf"
    default_color = "#ffffff"
    default_pos = "0"

    def __init__(self,
                 _name: str, 
                 _text: str = "",
                 fontPath: str = default_font, 
                 textColor: str = default_color,
                 x: str = default_pos, y: str = default_pos):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        text: str
            Text content of element
        fontPath: str
            Path of .bdf font file, relative to FONTS_PATH
        textColor: str
            Color of text, in hex format (with #), or as CSS3 color name
        x: int
            X-coordinate of bottom-left of text)
        y: int
            Y-coordinate of bottom-left of text)
        '''

        super().__init__(_name)
        self.text = Property(_text, str)
        try: 
            self.font = Property(fontPath, str, "s", 
                             [str(f)[len(FONTS_PATH):] for f in Path(FONTS_PATH).rglob("*.bdf")])
        except ValueError as ve: 
            self.font = Property(self.default_font, str, "s", 
                             [str(f)[len(FONTS_PATH):] for f in Path(FONTS_PATH).rglob("*.bdf")])
            log.warning(f"Font name invalid; set to default. ({ve})")
        self.color = Property("", str)
        # test color value formatting
        try: 
            if textColor.startswith("#"):
                webcolors.hex_to_rgb(textColor)
            else: 
                webcolors.name_to_rgb(textColor)
            self.color = Property(textColor, str)
        except ValueError as ve: 
            self.color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")
        self.pos = Property([int(x),int(y)], (int, int), "n2")

        # Define element var names
        # self._fontVarName = f"font_{self.name.value}"
        # self._colorVarName = f"color_{self.name.value}"

    def draw(self, canvas: FrameCanvas):# Prep vars for drawing
        _font = graphics.Font()
        _font.LoadFont(FONTS_PATH + self.font.value)
        colorRgb = colorFormat(self)
        _color = graphics.Color(*colorRgb)
        graphics.DrawText(canvas, 
                          _font,
                          self.pos.value[0], self.pos.value[1], 
                          _color,
                          self.text.value)
    
    def init_code(self) -> str: 
        return (f"{INIT_TAB}# TextElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Text: {self.text.value}\n"
                f"{INIT_TAB}#   Font: {self.font.value}\n"
                f"{INIT_TAB}#   Color: {self.color.value}\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}font_{self.name.value} = graphics.Font()\n"
                f"{INIT_TAB}font_{self.name.value}.LoadFont('{FONTS_PATH + self.font.value}')\n"
                f"{INIT_TAB}color_{self.name.value} = graphics.Color(*config.webcolor_to_rgb('{self.color.value}'))\n")

    def draw_code(self) -> str:
        colorRgb = colorFormat(self)
        return (f"{METHOD_TAB}graphics.DrawText(self.canvas,\n"
                f"{METHOD_TAB}    font_{self.name.value},\n"
                f"{METHOD_TAB}    {self.pos.value[0]}, {self.pos.value[1]},\n"
                f"{METHOD_TAB}    color_{self.name.value},\n"
                f"{METHOD_TAB}    \"{self.text.value}\")\n")

    def json(self):
        return self.__dict__

#endregion
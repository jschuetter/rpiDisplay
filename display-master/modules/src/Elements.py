#!/bin/python
# Import config module
import sys
sys.path.insert(0, "../..") # For config module
sys.path.insert(1, "../src") # For modules in this folder

import config
from config import FONTS_PATH

from copy import deepcopy
from typing import Any, NewType
import os, json

from rgbmatrix import FrameCanvas, graphics

from Property import Property
from elementhelpers import *

# Element dependencies
# IconElement
from PIL import Image
# TextElement
import webcolors
from pathlib import Path

class MatrixElement: 
    '''Parent class for all matrix elements

    SCHEMA
    Class variables: 
    - params [list]: list of params added using the `add_param` method
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
    - draw_code() [str]: returns Python code for drawing the element
        Always returns at indent level 1
    - json [dict]: returns element data as dict
    [Subclasses may also add methods if needed]
    '''

    params = [add_param("name", str, "Name of Element object (dev only).")]
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
        self.pos = Property((0,0), (int, int), "n2")
    
    def duplicate(self):
        return deepcopy(self)

    def draw(self, canvas: FrameCanvas):
        return None
    
    def draw_code(self, canvas: FrameCanvas) -> str:
        return None

    def json(self) -> dict:
        return self.__dict__

######## IMAGE ELEMENTS ########

class IconElement(MatrixElement):
    '''Element for displaying static bitmap images
    Requires .bmp filetype'''

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
        self.pos = Property((int(x),int(y)), (int, int), "n2")
        # self.x = int(x)
        # self.y = int(y)

    def draw(self, canvas: FrameCanvas):
        img = Image.open(self.path.value)
        img = img.convert("RGB")
        # print(self.pos.value)
        canvas.SetImage(img, self.pos.value[0], self.pos.value[1])
    
    def draw_code(self) -> str:
        return (f"    # IconElement '{self.name.value}'\n"
                f"    #   Path: {self.path.value}\n"
                f"    #   Pos: {self.pos.value}\n"
                f"    img = Image.open('{self.path.value}')\n"
                f"    img = img.convert('RGB')\n"
                f"    canvas.SetImage(img, {self.pos.value[0]}, {self.pos.value[1]})\n")

    def json(self):
        return self.__dict__

######## TEXT ELEMENTS ########

class TextElement(MatrixElement):
    '''Element for displaying static text
    Element size is determined by font and text content'''

    params = MatrixElement.params + [
        add_param("font", str, f"Font file to use, relative to base fonts path. \
                  Fonts may be found at '{FONTS_PATH}'"),
        add_param("textColor", str, "Hex value of font color to use (preceded by #). \
            Web color names may also be used. "),
        add_param("x_pos", int, "X-coordinate of icon (top-left)."),
        add_param("y_pos", int, "Y-coordinate of icon (top-left)")
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

    def __init__(self, 
                 _name: str, 
                 _text: str = "",
                 fontPath: str = "basic/4x6.bdf", 
                 textColor: str = "#ffffff",
                 x: str = "0", y: str = "0"):
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
        self.font = Property(fontPath, str, "s", 
                             [str(f)[len(FONTS_PATH):] for f in Path(FONTS_PATH).rglob("*.bdf")])
        self.color = Property("", str)
        # test color value formatting
        if textColor.startswith("#"):
            webcolors.hex_to_rgb(textColor)
        else: 
            webcolors.name_to_rgb(textColor)
        self.color = Property(textColor, str)
        self.pos = Property((int(x),int(y)), (int, int), "n2")

    def draw(self, canvas: FrameCanvas):
        font = graphics.Font()
        font.LoadFont(FONTS_PATH + self.font.value)

        # Format color value
        # try:
        #     if self.color.value.startswith("#"):
        #         colorRgb = webcolors.hex_to_rgb(self.color.value)
        #     else:
        #         colorRgb = webcolors.name_to_rgb(self.color.value)
        # except ValueError as e:
        #     print(e)
        #     print("Color defaulted to white.")
        #     self.color.value = "white"
        #     colorRgb = webcolors.name_to_rgb(self.color.value)
        colorRgb = colorFormat(self)

        color = graphics.Color(*colorRgb)
        graphics.DrawText(canvas, 
                          font,
                          self.pos.value[0], self.pos.value[1], 
                          color,
                          self.text.value)
    
    def draw_code(self) -> str:
        colorRgb = colorFormat(self)
        return (f"    # TextElement '{self.name.value}'\n"
                f"    #   Text: {self.text.value}\n"
                f"    #   Font: {self.font.value}\n"
                f"    #   Color: {self.color.value}\n"
                f"    #   Pos: {self.pos.value}\n"
                f"    myFont = graphics.Font()\n"
                f"    myFont.LoadFont('{FONTS_PATH + self.font.value}')\n"
                f"    graphics.DrawText(canvas,\n"
                f"        myFont,\n"
                f"        {self.pos.value[0]}, {self.pos.value[1]},\n"
                f"        graphics.Color(*{colorRgb}),\n"
                f"        \"{self.text.value}\")\n")

    def json(self):
        return self.__dict__
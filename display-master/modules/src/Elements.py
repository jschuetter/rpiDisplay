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
import os, json, math
from pathlib import Path

from rgbmatrix import FrameCanvas, graphics

from Property import Property
from Param import Parameter
from elementhelpers import *
from Components import *

# Element dependencies
# IconElement, Primitive elements
from PIL import Image, ImageDraw
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

#region primitiveElements

class RectElement(MatrixElement):
    '''Draws a rectangle.'''

    params = MatrixElement.params + [
        Parameter("x_pos", int, "X-coordinate of rect (top-left)."),
        Parameter("y_pos", int, "Y-coordinate of rect (top-left)"),
        Parameter("width", int, "Rectangle width"),
        Parameter("height", int, "Rectangle height (px)"),
        Parameter("fill_color", int, "Hex value of fill color to use (preceded by #). \
                    Web color names may also be used. "),
        Parameter("stroke_color", int, "Hex value of outline color to use (preceded by #). \
                    Web color names may also be used. ")
    ]
    docstr = "A rectangle.\n\n" + \
        "Usage: add rect [name] [x_pos] [y_pos] [width] [height] [fill_color] [stroke_color]\n\n" + \
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
        for e in args[1:5]:
            try:
                int(e)
            except ValueError: 
                return "Position and dimension arguments must be int values"
        # Color name may also be empty (default set in __init__)
        for arg in args[5:]:
            if arg == "": 
                pass
            elif arg.startswith("#"):
                try: 
                    webcolors.hex_to_rgb(arg)
                except ValueError:
                    return "Provided hex color is invalid."
            else: 
                try: 
                    webcolors.name_to_rgb(arg)
                except ValueError: 
                    return "Color value must be in hex, beginning with #, or \
                    a valid CSS3 color name. "
        # Return None if all arguments are valid
        return None
    
    default_color = "#ffffff"
    default_size = [10,10]
    default_pos = [0,0]
    
    def __init__(self, _name: str, x: str = "0", y: str = "0",
                width: str = "10", height: str = "10",
                fillColor: str = "white", strokeColor: str = "white"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        x: int
            X-coordinate of top-left of rect
        y: int
            Y-coordinate of top-left of rect
        width: int
            Width of rectangle in px
        height: int
            Height of rectangle in px
        fillColor: str
            Fill color of rectangle in hex or webcolor name
        strokeColor: str
            Stroke color of rectangle in hex or webcolor name
        '''

        super().__init__(_name)
        try: 
            self.pos = Property([int(x),int(y)], (int, int), "n2")
        except ValueError as ve: 
            self.pos = Property(self.default_pos, (int, int), "n2")
            log.warning(f"Position invalid; set to default. ({ve})")
        try: 
            self.size = Property([int(width),int(height)], (int, int), "n2")
        except ValueError as ve: 
            self.size = Property(self.default_size, (int, int), "n2")
            log.warning(f"Position invalid; set to default. ({ve})")
        self.fill_color = Property("", str)
        try: 
            if fillColor.startswith("#"):
                webcolors.hex_to_rgb(fillColor)
            else: 
                webcolors.name_to_rgb(fillColor)
            self.fill_color = Property(fillColor, str)
        except ValueError as ve: 
            self.fill_color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")

        self.stroke_color = Property("", str)
        try: 
            if strokeColor.startswith("#"):
                webcolors.hex_to_rgb(strokeColor)
            else: 
                webcolors.name_to_rgb(strokeColor)
            self.stroke_color = Property(strokeColor, str)
        except ValueError as ve: 
            self.stroke_color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")
        
    def draw(self, canvas: FrameCanvas):
        img = Image.new("RGB", (self.size.value[0] + 1, self.size.value[1] + 1))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, self.size.value[0], self.size.value[1]),
                        fill=self.fill_color.value, outline=self.stroke_color.value)
        canvas.SetImage(img, self.pos.value[0], self.pos.value[1])

    def init_code(self) -> str:
        imgVarname = f"img_{self.name.value}"
        return (f"{INIT_TAB}# RectElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}#   Size: {self.size.value}\n"
                f"{INIT_TAB}#   Fill color: {self.fill_color.value}\n"
                f"{INIT_TAB}#   Stroke color: {self.stroke_color.value}\n"
                f"{INIT_TAB}img_{self.name.value} = Image.new('RGB', ({self.size.value[0]+1}, {self.size.value[1]+1}))\n"
                f"{INIT_TAB}draw_{self.name.value} = ImageDraw.Draw(img_{self.name.value})\n"
                f"{INIT_TAB}draw_{self.name.value}.rectangle((0, 0, {self.size.value[0]}, {self.size.value[1]}), fill={self.fill_color.value}, outline={self.stroke_color.value})\n")
    
    def draw_code(self) -> str:
        return (
                f"{METHOD_TAB}self.canvas.SetImage(img_{self.name.value}, {self.pos.value[0]}, {self.pos.value[1]})\n")

    def json(self):
        return self.__dict__

class LineElement(MatrixElement):
    '''Draws a line.'''

    params = MatrixElement.params + [
        Parameter("x_1", int, "X-coordinate of line start"),
        Parameter("y_1", int, "Y-coordinate of line start"),
        Parameter("x_2", int, "X-coordinate of line end"),
        Parameter("y_2", int, "Y-coordinate of line end"),
        Parameter("Color", int, "Hex value of fill color to use (preceded by #). \
                    Web color names may also be used. "),
    ]
    docstr = "A line.\n\n" + \
        "Usage: add line [name] [x_1] [y_1] [x_2] [y_2] [Color]\n\n" + \
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
        for e in args[1:5]:
            try:
                int(e)
            except ValueError: 
                return "Position and dimension arguments must be int values"
        # Color name may also be empty (default set in __init__)
        if args[5] == "": 
            pass
        elif args[5].startswith("#"):
            try: 
                webcolors.hex_to_rgb(args[5])
            except ValueError:
                return "Provided hex color is invalid."
        else: 
            try: 
                webcolors.name_to_rgb(args[5])
            except ValueError: 
                return "Color value must be in hex, beginning with #, or \
                a valid CSS3 color name. "
        # Return None if all arguments are valid
        return None
    
    default_color = "#ffffff"
    
    def __init__(self, _name: str, x1: str = "0", y1: str = "0",
                x2: str = "0", y2: str = "0", lineColor: str = "white"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        x1: int
            X-coordinate of start of line
        y1: int
            Y-coordinate of start of line
        x2: int
            X-coordinate of end of line
        y2: int
            Y-coordinate of end of line
        lineColor: str
            Stroke color of line in hex or webcolor name
        '''

        super().__init__(_name)
        self.start = Property([int(x1),int(y1)], (int, int), "n2")
        self.end = Property([int(x2),int(y2)], (int, int), "n2")
        self.color = Property("", str)
        try: 
            if lineColor.startswith("#"):
                webcolors.hex_to_rgb(lineColor)
            else: 
                webcolors.name_to_rgb(lineColor)
            self.color = Property(lineColor, str)
        except ValueError as ve: 
            self.color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")

    def draw(self, canvas: FrameCanvas):
        colorRgb = colorFormat(self)
        _color = graphics.Color(*colorRgb)
        graphics.DrawLine(canvas, 
                          self.start.value[0], self.start.value[1], 
                          self.end.value[0], self.end.value[1], 
                          _color)
    

    def init_code(self) -> str:
        imgVarname = f"img_{self.name.value}"
        return (f"{INIT_TAB}# LineElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Start: {self.start.value}\n"
                f"{INIT_TAB}#   End: {self.end.value}\n"
                f"{INIT_TAB}#   Stroke color: {self.color.value}\n"
                f"{INIT_TAB}color_{self.name.value} = graphics.Color(*config.webcolor_to_rgb('{self.color.value}'))\n")
    
    def draw_code(self) -> str:
        return (f"{METHOD_TAB}graphics.DrawLine(self.canvas,\n"
                f"{METHOD_TAB}    {self.start.value[0]}, {self.start.value[1]},\n"
                f"{METHOD_TAB}    {self.end.value[0]}, {self.end.value[1]},\n"
                f"{METHOD_TAB}    color_{self.name.value},\n")

    def json(self):
        return self.__dict__


class EllipseElement(MatrixElement):
    '''Draws an ellipse.'''

    params = MatrixElement.params + [
        Parameter("x_pos", int, "X-coordinate of ellipse (top-left)."),
        Parameter("y_pos", int, "Y-coordinate of ellipse (top-left)"),
        Parameter("width", int, "Ellipse width"),
        Parameter("height", int, "Ellipse height (px)"),
        Parameter("fill_color", int, "Hex value of fill color to use (preceded by #). \
                    Web color names may also be used. "),
        Parameter("stroke_color", int, "Hex value of outline color to use (preceded by #). \
                    Web color names may also be used. ")
    ]
    docstr = "An ellipse.\n\n" + \
        "Usage: add ellipse [name] [x_pos] [y_pos] [width] [height] [fill_color] [stroke_color]\n\n" + \
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
        for e in args[1:5]:
            try:
                int(e)
            except ValueError: 
                return "Position and dimension arguments must be int values"
        # Color name may also be empty (default set in __init__)
        for arg in args[5:]:
            if arg == "": 
                pass
            elif arg.startswith("#"):
                try: 
                    webcolors.hex_to_rgb(arg)
                except ValueError:
                    return "Provided hex color is invalid."
            else: 
                try: 
                    webcolors.name_to_rgb(arg)
                except ValueError: 
                    return "Color value must be in hex, beginning with #, or \
                    a valid CSS3 color name. "
        # Return None if all arguments are valid
        return None
    
    default_color = "#ffffff"
    default_size = [10,10]
    default_pos = [0,0]
    
    def __init__(self, _name: str, x: str = "0", y: str = "0",
                width: str = "10", height: str = "10",
                fillColor: str = "white", strokeColor: str = "white"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        x: int
            X-coordinate of top-left of ellipse
        y: int
            Y-coordinate of top-left of ellipse
        width: int
            Width of ellipse in px
        height: int
            Height of ellipse in px
        fillColor: str
            Fill color of ellipse in hex or webcolor name
        strokeColor: str
            Stroke color of ellipse in hex or webcolor name
        '''

        super().__init__(_name)
        try: 
            self.pos = Property([int(x),int(y)], (int, int), "n2")
        except ValueError as ve: 
            self.pos = Property(self.default_pos, (int, int), "n2")
            log.warning(f"Position invalid; set to default. ({ve})")
        try: 
            self.size = Property([int(width),int(height)], (int, int), "n2")
        except ValueError as ve: 
            self.size = Property(self.default_size, (int, int), "n2")
            log.warning(f"Position invalid; set to default. ({ve})")
        self.fill_color = Property("", str)
        try: 
            if fillColor.startswith("#"):
                webcolors.hex_to_rgb(fillColor)
            else: 
                webcolors.name_to_rgb(fillColor)
            self.fill_color = Property(fillColor, str)
        except ValueError as ve: 
            self.fill_color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")

        self.stroke_color = Property("", str)
        try: 
            if strokeColor.startswith("#"):
                webcolors.hex_to_rgb(strokeColor)
            else: 
                webcolors.name_to_rgb(strokeColor)
            self.stroke_color = Property(strokeColor, str)
        except ValueError as ve: 
            self.stroke_color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")
        
    def draw(self, canvas: FrameCanvas):
        # img = Image.new("RGB", (self.size.value[0] + 1, self.size.value[1] + 1))
        # draw = ImageDraw.Draw(img)
        # draw.ellipse((0, 0, self.size.value[0], self.size.value[1]),
        #                 fill=self.fill_color.value, outline=self.stroke_color.value)
        # canvas.SetImage(img, self.pos.value[0], self.pos.value[1])
        component = Ellipse(
            self.pos.value[0], self.pos.value[1],
            self.size.value[0], self.size.value[1], 
            fill=config.webcolor_to_rgb(self.fill_color.value), 
            stroke=config.webcolor_to_rgb(self.stroke_color.value), 
        )
        component.draw(canvas)

    def init_code(self) -> str:
        imgVarname = f"img_{self.name.value}"
        return (f"{INIT_TAB}# EllipseElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}#   Size: {self.size.value}\n"
                f"{INIT_TAB}#   Fill color: {self.fill_color.value}\n"
                f"{INIT_TAB}#   Stroke color: {self.stroke_color.value}\n"
                f"{INIT_TAB}img_{self.name.value} = Image.new('RGB', ({self.size.value[0]+1}, {self.size.value[1]+1}))\n"
                f"{INIT_TAB}draw_{self.name.value} = ImageDraw.Draw(img_{self.name.value})\n"
                f"{INIT_TAB}draw_{self.name.value}.ellipse((0, 0, {self.size.value[0]}, {self.size.value[1]}), fill={self.fill_color.value}, outline={self.stroke_color.value})\n")
    
    def draw_code(self) -> str:
        return (
                f"{METHOD_TAB}self.canvas.SetImage(img_{self.name.value}, {self.pos.value[0]}, {self.pos.value[1]})\n")

    def json(self):
        return self.__dict__

class CircleElement(MatrixElement):
    '''Draws an circle.'''

    params = MatrixElement.params + [
        Parameter("x_pos", int, "X-coordinate of icon (top-left)."),
        Parameter("y_pos", int, "Y-coordinate of icon (top-left)"),
        Parameter("radius", int, "Circle radius (px)"),
        Parameter("color", int, "Hex value of fill color to use (preceded by #). \
                    Web color names may also be used. ")
    ]
    docstr = "A circle.\n\n" + \
        "Usage: add ellipse [name] [x_pos] [y_pos] [width] [height] [color]\n\n" + \
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
        for e in args[1:4]:
            try:
                int(e)
            except ValueError: 
                return "Position and dimension arguments must be int values"
        # Color name may also be empty (default set in __init__)
        for arg in args[4:]:
            if arg == "": 
                pass
            elif arg.startswith("#"):
                try: 
                    webcolors.hex_to_rgb(arg)
                except ValueError:
                    return "Provided hex color is invalid."
            else: 
                try: 
                    webcolors.name_to_rgb(arg)
                except ValueError: 
                    return "Color value must be in hex, beginning with #, or \
                    a valid CSS3 color name. "
        # Return None if all arguments are valid
        return None
    
    default_color = "#ffffff"
    default_size = [10,10]
    default_pos = [0,0]
    
    def __init__(self, _name: str, x: str = "0", y: str = "0",
                rad: str = "10",
                fillColor: str = "white", strokeColor: str = "white"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        x: int
            X-coordinate of top-left of circle
        y: int
            Y-coordinate of top-left of circle
        rad: int
            Radius of circle in px
        fillColor: str
            Fill color of circle in hex or webcolor name
        '''

        super().__init__(_name)
        try: 
            self.pos = Property([int(x),int(y)], (int, int), "n2")
        except ValueError as ve: 
            self.pos = Property(self.default_pos, (int, int), "n2")
            log.warning(f"Position invalid; set to default. ({ve})")
        try: 
            self.radius = Property(int(rad), (int, int), "n2")
        except ValueError as ve: 
            self.size = Property(self.default_size, int, "n")
            log.warning(f"Radius invalid; set to default. ({ve})")
        self.color = Property("", str)
        try: 
            if fillColor.startswith("#"):
                webcolors.hex_to_rgb(fillColor)
            else: 
                webcolors.name_to_rgb(fillColor)
            self.color = Property(fillColor, str)
        except ValueError as ve: 
            self.color = Property(self.default_color, str)
            log.warning(f"Color invalid; set to default. ({ve})")

    def draw(self, canvas: FrameCanvas):
        colorRgb = colorFormat(self)
        _color = graphics.Color(*colorRgb)
        graphics.DrawCircle(canvas, 
                          self.pos.value[0], self.pos.value[1], 
                          self.radius.value, 
                          _color)

    def init_code(self) -> str:
        imgVarname = f"img_{self.name.value}"
        return (f"{INIT_TAB}# CircleElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}#   Radius: {self.radius.value}\n"
                f"{INIT_TAB}#   Fill color: {self.color.value}\n"
                f"{INIT_TAB}color_{self.name.value} = graphics.Color(*config.webcolor_to_rgb('{self.color.value}'))\n")

    
    def draw_code(self) -> str:
        return (f"{METHOD_TAB}graphics.DrawCircle(self.canvas,\n"
                f"{METHOD_TAB}    {self.pos.value[0]}, {self.pos.value[1]},\n"
                f"{METHOD_TAB}    {self.radius.value},\n"
                f"{METHOD_TAB}    color_{self.name.value},\n")

    def json(self):
        return self.__dict__


#endregion

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
        # if not os.path.isfile(imgPath): 
        #     raise ValueError("Invalid path.")
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

class ImageElement(MatrixElement):
    '''Element for displaying static pixel-space images
    Requires .jpg or .png filetype'''

    params = MatrixElement.params + [
        Parameter("path", str, "Relative path to the default icon for this object. " +
                  "Icon must be in .bmp format."),
        Parameter("x_pos", int, "X-coordinate of icon (top-left)."),
        Parameter("y_pos", int, "Y-coordinate of icon (top-left)"),
        Parameter("size", int, "Pixel width of image")
    ]
    docstr = "An image.\n\n" + \
        "Usage: add image [name] [path] [x_pos] [y_pos] [size]\n\n" + \
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
        # elif not args[1].endswith(".bmp"):
        #     return "Image type must be .bmp (use Image class for pixel types)."
        for e in args[2:5]:
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

    def __init__(self, _name: str, imgPath: str = "", 
                x: str = "0", y: str = "0", 
                width: str = "32"):
        '''
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        imgPath: str
            Path of image file to show
        x: int
            X-coordinate of top-left of image
        y: int
            Y-coordinate of top-left of image
        size: int
            Size at which to display image (aspect ratio locked)
            Defaults to 32 px
        '''

        super().__init__(_name)
        # if not os.path.isfile(imgPath): 
        #     raise ValueError("Invalid path.")
        self.path = Property(imgPath, str)
        for arg in (x,y): 
            if arg == "": 
                arg = "0"
        self.pos = Property([int(x),int(y)], (int, int), "n2")
        if width == "": 
            width = "32"
        self.size = Property(int(width), int, "n")
        # self.height = None # Initialized on loading image for first time
        
    def draw(self, canvas: FrameCanvas):
        img = Image.open(self.path.value)
        # if not self.height: 
        #     w, h = img.size
        #     self.height = Property(math.ceil(self.width.value * (h/w)), int, "n")
        img.thumbnail((self.size.value, self.size.value), Image.ANTIALIAS)
        img = img.convert("RGB")
        canvas.SetImage(img, self.pos.value[0], self.pos.value[1])

    def init_code(self) -> str:
        imgVarname = f"img_{self.name.value}"
        return (f"{INIT_TAB}# ImageElement '{self.name.value}'\n"
                f"{INIT_TAB}#   Path: {self.path.value}\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}#   Size: {self.size.value}\n"
                f"{INIT_TAB}img_{self.name.value} = Image.open('{self.path.value}')"
                f".thumbnail(({self.size.value}, {self.size.value}), Image.ANTIALIAS)"
                f".convert('RGB')\n")
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
        Parameter("font_family", str, f"Directory of fonts to use, relative to base fonts path. \
                    Fonts may be found at '{FONTS_PATH}'"),
        Parameter("font", str, f"Font file to use, relative to font family directory path. \
                    Must exist in directory specified by `font_family`. \
                    If no font is specified, one is chosen at runtime using `glob.glob`. \
                    Fonts may be found at '{FONTS_PATH}'"),
        Parameter("textColor", str, "Hex value of font color to use (preceded by #). \
                    Web color names may also be used. "),
        Parameter("x_pos", int, "X-coordinate of icon (top-left)"),
        Parameter("y_pos", int, "Y-coordinate of icon (top-left)")
    ]
    docstr = "Static text.\n\n" + \
        "Usage: add text [name] [textContent] [font] [textColor] [x_pos] [y_pos]\n\n" + \
            print_params(params)
    
    # Valid font file extension
    font_type = ".bdf"

    @classmethod
    def testArgs(cls, *args):
        '''Tests validity of arguments. 
        Returns string response if invalid args. 
        Returns None if valid.'''
        if len(args) < len(cls.params): 
            return "Incorrect number of args."
        # Arg 0: element name
        if not isinstance(args[0], str):
            return "Invalid element name."
        # Arg 1: text contents
        if not isinstance(args[1], str):
            return "Text content must be str."
        # Arg 2: font_family
        fontFamilyPath = FONTS_PATH + args[2]
        if not os.path.isdir(fontFamilyPath): 
            return "Invalid font family."
        # Arg 3: font path
        fontPath = os.path.join(FONTS_PATH, args[2], args[3])
        # Font path may be empty (default set in __init__)
        if args[3] == "": 
            pass
        elif (
            not os.path.isfile(fontPath)
            or not fontPath.endswith(cls.font_type)
            or not Path(fontPath).is_relative_to(Path(fontFamilyPath))
            ): 
            return "Invalid font path."
        # Arg 4: color (name or hex)
        # Color name may also be empty (default set in __init__)
        if args[4] == "": 
            pass
        elif args[4].startswith("#"):
            try: 
                webcolors.hex_to_rgb(args[4])
            except ValueError:
                return "Provided hex color is invalid."
        else: 
            try: 
                webcolors.name_to_rgb(args[4])
            except ValueError: 
                return "Color value must be in hex, beginning with #, or \
                a valid CSS3 color name. "
        # Args 5 & 6: position
        for e in args[5:7]:
            try:
                int(e)
            except ValueError: 
                return "Position arguments must be int values"
        # Return None if all arguments are valid
        return None

    default_font_family = "basic"
    default_font = "4x6.bdf"
    default_color = "#ffffff"
    default_pos = "0"
    @classmethod 
    def get_valid_font_families(cls): 
        return [str(d) for d in os.listdir(FONTS_PATH)
                    if os.path.isdir(os.path.join(FONTS_PATH, d))]
    @classmethod
    def get_valid_fonts(cls, family): 
        fontFamilyPath = os.path.join(FONTS_PATH, family)
        # Output files w/ prefixes cut off --
        #   add 1 to length of path to ignore join symbol
        return [str(f)[len(fontFamilyPath)+1:] for f 
                    in Path(fontFamilyPath).rglob(f"*{cls.font_type}")]

    # Helper methods for getting font information
    def get_font_path(self): 
        '''Returns path of selected font, relative to base fonts path'''
        return os.path.join(FONTS_PATH, self.font_family.value, self.font.value)
    def refresh_font(self): 
        '''Refreshes valid fonts & families lists & re-selects default font if needed.
            Used for maintaining integrity while editing.
            N.B. valid font families should not change unless 
            file structure is altered during runtime (desired exception).'''
        valid_fonts = self.get_valid_fonts(self.font_family.value)
        if self.font.value not in valid_fonts: 
            # Select new default font if needed
            self.font = Property(valid_fonts[0], str, "s", valid_fonts)
            log.debug(f"New default font selected ({self.get_font_path()})")



    def __init__(self,
                 _name: str, 
                 _text: str = "",
                 fontFamily: str = default_font_family,
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
        fontFamily: str
            Path of font directory, relative to FONTS_PATH
            Default value: YES
        fontPath: str
            Path of .bdf font file, relative to FONTS_PATH
            Default value: YES
        textColor: str
            Color of text, in hex format (with #), or as CSS3 color name
            Default value: YES
        x: int
            X-coordinate of bottom-left of text)
        y: int
            Y-coordinate of bottom-left of text)
        '''

        super().__init__(_name)
        self.text = Property(_text, str)

        # Set font family - default if invalid
        valid_font_families = self.get_valid_font_families()
        try: 
            self.font_family = Property(fontFamily, str, "s", 
                             valid_font_families)
        except ValueError as ve: 
            self.font_family = Property(self.default_font_family, str, "s", 
                             valid_font_families)
            log.warning(f"Font family invalid; set to default. ({ve})")

        # Set font within family - select automatically if invalid
        valid_fonts = self.get_valid_fonts(self.font_family.value)
        try: 
            # Raise exception if font path is not in font family
            if fontPath not in valid_fonts: 
                raise ValueError
                
            self.font = Property(fontPath, str, "s", valid_fonts)
        except ValueError as ve: 
            # If font name is invalid, set font to first in valid list
            self.font = Property(valid_fonts[0], str, "s", valid_fonts)
            log.warning(f"Font name unspecified or invalid; set to default. ({ve})")
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
        # Refresh valid fonts & families; select new default font if needed
        self.refresh_font()
        _font = graphics.Font()
        _font.LoadFont(self.get_font_path())
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
                f"{INIT_TAB}#   Font: {self.get_font_path()}\n"
                f"{INIT_TAB}#   Color: {self.color.value}\n"
                f"{INIT_TAB}#   Pos: {self.pos.value}\n"
                f"{INIT_TAB}font_{self.name.value} = graphics.Font()\n"
                f"{INIT_TAB}font_{self.name.value}.LoadFont('{self.get_font_path()}')\n"
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
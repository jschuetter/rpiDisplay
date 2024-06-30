#!/bin/python
from rgbmatrix import FrameCanvas
from copy import deepcopy
from typing import Any, NewType
from PIL import Image

class Property:
    """Custom class for MatrixElement properties

    Allows adding use data along with each variable
    - 
    - Allowed Property modes: 
        - l (literal): assignable by literal value only
        - s (scrollable): can scroll through list of allowed values in editor
        - n (numeric): can use arrow keys to increment/decrement values
        - n2 (numeric tuple): can use arrow keys (left/right, up/down) to 
            increment/decrement each tuple value respectively
    """

    allowedModes = ["l", "s", "n", "n2"]
    def __init__(self, _value: Any, _mode: str = "l", _opt: list = []):
        """
        Parameters
        ----------
        _value: Any
            Value of parameter
        _mode: str
            parameter mode (see class docstring)
        _opt: list[str]
            list of available value options
            Required for "scrollable" mode
        """

        self.value = _value
        if _mode not in self.allowedModes: 
            raise ValueError("Invalid mode string")
        self.mode = _mode
        if self.mode == "s" and _opt == []:
            raise ValueError("Options list is required for scrollable mode.")
        self.options = _opt

class MatrixElement: 
    def __init__(self, _name: str):
        """
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        """

        self.name = _name
        self.group = []
        self.pos = Property((0,0), "n2")
    
    def duplicate(self):
        return deepcopy(self)

# Element for displaying static bitmap images
# Requires .bmp filetype
class IconElement(MatrixElement):
    def __init__(self, _name: str, imgPath: str = "", _pos: tuple = (0,0)):
        """
        Parameters
        ----------
        _name: str
            Element name - must be unique among sibling Elements
        imgPath: str
            Path of .bmp file to show
        _pos: tuple[int, int]
            Tuple (x,y) of position to display image (coordinate of top-left of image)
        """

        super().__init__(_name)
        self.path = imgPath
        self.pos = _pos

    def draw(self, canvas: FrameCanvas):
        img = Image.open(self.path)
        img = img.convert("RGB")
        canvas.SetImage(img, self.pos[0], self.pos[1])

    def json(self):
        return self.__dict__
# 

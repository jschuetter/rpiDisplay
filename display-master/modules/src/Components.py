#!/bin/python
'''
Components.py
Definition of Component classes
Similar to Element classes, but stripped-down for final implementation
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
from typeguard import typechecked

from rgbmatrix import FrameCanvas, graphics

from Property import Property
from Param import Parameter
from elementhelpers import *

# Element dependencies
# Primitive elements 
import numpy as np
# IconElement, Primitive elements
from PIL import Image, ImageDraw
# TextElement
import webcolors
from pathlib import Path

class Component():
    '''Parent class for all Component objects'''

    @typechecked
    def __init__(self, x_: int = 0, y_: int = 0):
        '''
        Parameters
        ------------
        x: int
            x-coordinate (relative to top-left)
        y: int
            y-coordinate (relative to top-left)'''
        self.x = x_
        self.y = y_

    def draw(self, canvas: FrameCanvas):
        pass

    def loop(self, canvas: FrameCanvas):
        self.draw(canvas)

    def duplicate(self):
        return deepcopy(self)

#region primitive elements

class PrimitiveComponent(Component): 
    '''
    Parent class for primitive elements.
    Includes features like width/height dimensions, 
    fill/stroke colors, etc.
    '''

    @typechecked
    def __init__(self, x_: int, y_: int, w: int, h: int, fillColor: tuple = (255,255,255), 
                strokeColor: tuple = (255,255,255), strokeWeight: int = 0):
        '''
        Parameters
        ------------
        x: int (relative to top-left)
            x-position
        y: int (relative to top-left)
            y-position
        w: int
            width of rectangle (px)
        h: int
            height of rectangle (px)
        fillColor: tuple
            (r,g,b) value of fill color
        strokeColor: tuple
            (r,g,b) value of stroke color (applied *inside* specified width/height)
        strokeWeight: int
            Width of stroke in px (applied *inside* specified width/height)
        '''

        super().__init__(x_, y_)
        
        if w <= 0 or h <= 0: 
            raise ValueError("Dimensions must be greater than 0!")
        self.width = w
        self.height = h

        for colorValue in (fillColor, strokeColor):
            if not isinstance(colorValue, tuple) or len(colorValue) != 3:
                raise ValueError("Colors must be specified in tuples of length 3")
            for val in colorValue:
                if val < 0 or val > 255:
                    raise ValueError("Color values must be in [0,255]")
        self.fill_color = fillColor
        self.stroke_color = strokeColor

        if strokeWeight < 0: 
            raise ValueError("Stroke weight cannot be negative")
        elif strokeWeight > self.height // 2: 
            raise ValueError(f"Stroke weight cannot be greater than half the height ({self.height//2})")
        self.stroke_weight = strokeWeight

class HollowPrimitiveComponent(Component): 
    '''
    Parent class for hollow primitive elements.
    Same as PrimitiveComponent class, without fillColor paremeter.
    '''

    @typechecked
    def __init__(self, x_: int, y_: int, w: int, h: int, strokeColor: tuple = (255,255,255), 
                strokeWeight: int = 0):
        '''
        Parameters
        ------------
        x: int
            x-position (relative to top-left)
        y: int
            y-position (relative to top-left)
        w: int
            width of rectangle (px)
        h: int
            height of rectangle (px)
        strokeColor: tuple
            (r,g,b) value of stroke color (applied *inside* specified width/height)
        strokeWeight: int
            Width of stroke in px (applied *inside* specified width/height)
        '''

        super().__init__(x_, y_)
        
        if w <= 0 or h <= 0: 
            raise ValueError("Dimensions must be greater than 0!")
        self.width = w
        self.height = h

        if not isinstance(strokeColor, tuple) or len(strokeColor) != 3:
            raise ValueError("Colors must be specified in tuples of length 3")
        for val in strokeColor:
            if val < 0 or val > 255:
                raise ValueError("Color values must be in [0,255]")
        self.stroke_color = strokeColor

        if strokeWeight < 0: 
            raise ValueError("Stroke weight cannot be negative")
        elif strokeWeight > self.height // 2: 
            raise ValueError(f"Stroke weight cannot be greater than half the height ({self.height//2})")
        self.stroke_weight = strokeWeight

class Rect(PrimitiveComponent): 
    '''Draws a rectangle.'''

    def draw(self, canvas: FrameCanvas):
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                # Check if pixel is inside stroke
                if (
                    (x < self.x + self.stroke_weight or 
                    x >= self.x + self.width - self.stroke_weight) or 
                    (y < self.y + self.stroke_weight or 
                    y >= self.y + self.height - self.stroke_weight) 
                ):
                    canvas.SetPixel(x, y, *self.stroke_color)
                else: 
                    canvas.SetPixel(x, y, *self.fill_color)

class RectHollow(HollowPrimitiveComponent): 
    '''Draws a rectangle.'''

    def draw(self, canvas: FrameCanvas):
        # Find values inside stroke
        stroke_y = set(
            range(self.y, self.y + self.stroke_weight)
        ).union(
            range(self.y + self.height - self.stroke_weight, self.y + self.height)
        )
        stroke_x = set(
            range(self.x, self.x + self.stroke_weight)
        ).union(
            range(self.x + self.width - self.stroke_weight, self.x + self.width)
        )
        for y in stroke_y:
            for x in range(self.x, self.x + self.width): 
                canvas.SetPixel(x, y, *self.stroke_color)
        for x in stroke_x:
            for y in range(self.y, self.y + self.height):
                canvas.SetPixel(x, y, *self.stroke_color)

class Ellipse(PrimitiveComponent): 
    '''Draws an ellipse'''
    tolerance = 0.05    # Makes ellipses look a little better

    def draw(self, canvas: FrameCanvas):
        # Find values required for ellipse plotting equation
        ctrX = self.x + self.width / 2
        ctrY = self.y + self.height / 2
        axisA = self.width / 2
        axisB = self.height / 2

        # Create Numpy grid to match matrix
        gridX, gridY = np.ogrid[:canvas.width, :canvas.height]

        # Use ellipse equation to create grid masks
        strokeMask = ((gridX - ctrX) / axisA) ** 2 + ((gridY - ctrY) / axisB) **2 <= 1 + self.tolerance
        strokePts = np.argwhere(strokeMask)
        # Calculate fill mask based on stroke mask
        ptsX = strokePts[:,0]
        ptsY = strokePts[:,1]
        fillMask = ((ptsX - ctrX) / (axisA - self.stroke_weight)) ** 2 + ((ptsY - ctrY) / (axisB - self.stroke_weight)) ** 2 <= 1 + self.tolerance
        fillPts = strokePts[fillMask]
        # Flip coord order & convert to sets to remove 
        fillPts = set(map(tuple, fillPts))
        strokePts = set(map(tuple, strokePts)) - fillPts

        for (x_, y_) in strokePts: 
            canvas.SetPixel(x_, y_, *self.stroke_color)
        for (x_, y_) in fillPts: 
            canvas.SetPixel(x_, y_, *self.fill_color)

class EllipseHollow(HollowPrimitiveComponent): 
    '''Draws an ellipse'''
    tolerance = 0.05    # Makes ellipses look a little better

    def draw(self, canvas: FrameCanvas):
        # Find values required for ellipse plotting equation
        ctrX = self.x + self.width / 2
        ctrY = self.y + self.height / 2
        axisA = self.width / 2
        axisB = self.height / 2

        # Create Numpy grid to match matrix
        gridX, gridY = np.ogrid[:canvas.width, :canvas.height]

        # Use ellipse equation to create grid masks
        strokeMask = ((gridX - ctrX) / axisA) ** 2 + ((gridY - ctrY) / axisB) **2 <= 1 + self.tolerance
        strokePts = np.argwhere(strokeMask)
        # Calculate fill mask based on stroke mask
        ptsX = strokePts[:,0]
        ptsY = strokePts[:,1]
        fillMask = ((ptsX - ctrX) / (axisA - self.stroke_weight)) ** 2 + ((ptsY - ctrY) / (axisB - self.stroke_weight)) ** 2 <= 1 + self.tolerance
        fillPts = strokePts[fillMask]
        # Flip coord order & convert to sets to remove fill
        strokePts = set(map(tuple, strokePts)) - set(map(tuple, fillPts))

        for (x_, y_) in strokePts: 
            canvas.SetPixel(x_, y_, *self.stroke_color)
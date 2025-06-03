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
from typing import Union, Optional

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

#region primitive components

class PrimitiveComponent(Component): 
    '''
    Parent class for primitive elements.
    Includes features like width/height dimensions, 
    fill/stroke colors, etc.
    '''

    def getFillPts(self):
        self.fill_pts = ()
    def getStrokePts(self): 
        self.stroke_pts = ()

    @typechecked
    def __init__(self, x_: int, y_: int, w: int, h: int, 
                fillColor: Union[tuple, None] = (255,255,255), 
                strokeColor: Union[tuple, None] = (255,255,255), 
                strokeWeight: int = 0,
                *, 
                noFill: bool = False): 
        '''
        Parameters
        ------------
        x: int (relative to top-left)
            x-position
        y: int (relative to top-left)
            y-position
        w: int
            width (px)
        h: int
            height (px)
        fillColor: tuple | None
            (r,g,b) value of fill color
            If None: sets no_fill to True
        strokeColor: tuple
            (r,g,b) value of stroke color (applied *inside* specified width/height)
            If None: sets stroke_weight to 0
        strokeWeight: int
            Width of stroke in px (applied *inside* specified width/height)
        noFill: bool
            Skip drawing fill of shape (defaults to False)
        rotateDegrees: int
            Number of degrees to rotate about shape origin
        ----------------
        Other Attributes
        ----------------
        fill_pts: points in the fill space of the Primitive, stored as a 
            tuple of tuples
        stroke_pts: points in the stroke space of the Primitive, stored as
            a tuple of tuples
        '''

        super().__init__(x_, y_)
        
        if w <= 0 or h <= 0: 
            raise ValueError("Dimensions must be greater than 0!")
        self.width = w
        self.height = h

        for colorValue in (fillColor, strokeColor):
            if colorValue is not None: 
                if not isinstance(colorValue, tuple) or len(colorValue) != 3:
                    raise ValueError("Colors must be specified in tuples of length 3")
                for val in colorValue:
                    if val < 0 or val > 255:
                        raise ValueError("Color values must be in [0,255]")
        self.fill_color = fillColor
        self.stroke_color = strokeColor

        if self.stroke_color is None: 
            self.stroke_weight = 0
        else: 
            if strokeWeight < 0: 
                raise ValueError("Stroke weight cannot be negative")
            elif strokeWeight > self.height // 2: 
                raise ValueError(f"Stroke weight cannot be greater than half the height ({self.height//2})")
            self.stroke_weight = strokeWeight

        if self.fill_color is None: 
            self.no_fill = True
        else: 
            self.no_fill = noFill

        self.rotation = rotateDegrees

        # Store coordinates of each point in shape
        self.getFillPts()
        self.getStrokePts()

    def draw(self, canvas: FrameCanvas):
        if not self.fill_pts and not self.no_fill: 
            self.getFillPts()
        if not self.stroke_pts and self.stroke_weight > 0: 
            self.getStrokePts()

        if not self.no_fill: 
            for pX, pY in self.fill_pts: 
                canvas.SetPixel(pX, pY, *self.fill_color)
        if self.stroke_weight > 0: 
            for pX, pY in self.stroke_pts: 
                canvas.SetPixel(pX, pY, *self.stroke_color)

class Rect(PrimitiveComponent): 
    '''Draws a rectangle.'''

    def getFillPts(self):
        # If do_fill is False, return empty
        if self.no_fill: 
            self.fill_pts = ()
            return

        fillX = self.x + self.stroke_weight
        fillY = self.y + self.stroke_weight
        fillW = self.width - 2 * self.stroke_weight
        fillH = self.height - 2 * self.stroke_weight
        xArr, yArr = np.meshgrid(
            np.arange(fillX, fillX + fillW),
            np.arange(fillY, fillY + fillH)
        )
        self.fill_pts = tuple(zip(xArr.ravel(), yArr.ravel()))

    def getStrokePts(self): 
        # If stroke weight is 0, return empty
        if self.stroke_weight == 0: 
            self.stroke_pts = ()
            return

        # Calculate horizontal parts first
        horizX = np.arange(self.x, self.x + self.width)
        topY = np.arange(self.y, self.y + self.stroke_weight)
        bottomY = np.arange(
            self.y + self.height - self.stroke_weight,
            self.y + self.height
            )
        hX, hY = np.meshgrid(
            horizX, 
            np.concatenate([topY, bottomY])
        )
        horizPts = tuple(zip(hX.ravel(), hY.ravel()))

        # Calculate vertical sides
        leftX = np.arange(self.x, self.x + self.stroke_weight)
        rightX = np.arange(
            self.x + self.width - self.stroke_weight, 
            self.x + self.width
            )
        vertY = np.arange(
            self.y + self.stroke_weight,
            self.y + self.height - self.stroke_weight
            )
        vX, vY = np.meshgrid(
            np.concatenate([leftX, rightX]), 
            vertY
        )
        vertPts = tuple(zip(vX.ravel(), vY.ravel()))

        # Return concatenation of horizontal & vertical sides
        self.stroke_pts = horizPts + vertPts

    # def draw(self, canvas: FrameCanvas):
    #     if not self.no_fill: 
    #         for pX, pY in self.fill_pts: 
    #             canvas.SetPixel(pX, pY, *self.fill_color)
    #     for pX, pY in self.stroke_pts: 
    #         canvas.SetPixel(pX, pY, *self.stroke_color)
    #     for y in range(self.y, self.y + self.height):
    #         for x in range(self.x, self.x + self.width):
    #             # Check if pixel is inside stroke
    #             if (
    #                 (x < self.x + self.stroke_weight or 
    #                 x >= self.x + self.width - self.stroke_weight) or 
    #                 (y < self.y + self.stroke_weight or 
    #                 y >= self.y + self.height - self.stroke_weight) 
    #             ):
    #                 canvas.SetPixel(x, y, *self.stroke_color)
    #             elif self.do_fill: 
    #                 canvas.SetPixel(x, y, *self.fill_color)

class Ellipse(PrimitiveComponent): 
    '''Draws an ellipse'''
    tolerance = 0.05    # Makes ellipses look a little better

    def getAllPts(self): 
        '''
        Helper method for getting points -- requires finding
        both fill and stroke points
        '''
        # Find values required for ellipse plotting equation
        ctrX = self.x + self.width / 2
        ctrY = self.y + self.height / 2
        axisA = self.width / 2
        axisB = self.height / 2

        # Create Numpy grid to match matrix
        # Get canvas width & height from environment vars
        canvasH = int(os.getenv("MATRIX_ROWS", 32))
        canvasW = int(os.getenv("MATRIX_COLS", 32))
        gridX, gridY = np.ogrid[:canvasW, :canvasH]

        # Use ellipse equation to create grid masks
        strokeMask = ((gridX - ctrX) / axisA) ** 2 + ((gridY - ctrY) / axisB) **2 <= 1 + self.tolerance
        strokePts = np.argwhere(strokeMask)
        # Calculate fill mask based on stroke mask
        ptsX = strokePts[:,0]
        ptsY = strokePts[:,1]
        fillMask = ((ptsX - ctrX) / (axisA - self.stroke_weight)) ** 2 + ((ptsY - ctrY) / (axisB - self.stroke_weight)) ** 2 <= 1 + self.tolerance
        fillPts = strokePts[fillMask]
        # Flip coord order & convert to sets to remove 
        self.fill_pts = set(map(tuple, fillPts))
        self.stroke_pts = set(map(tuple, strokePts)) - self.fill_pts

    # Alias both getter methods to getAllPts()
    def getFillPts(self): 
        self.getAllPts()
    def getStrokePts(self): 
        self.getAllPts()

    # def draw(self, canvas: FrameCanvas):
    #     # Find values required for ellipse plotting equation
    #     ctrX = self.x + self.width / 2
    #     ctrY = self.y + self.height / 2
    #     axisA = self.width / 2
    #     axisB = self.height / 2

    #     # Create Numpy grid to match matrix
    #     gridX, gridY = np.ogrid[:canvas.width, :canvas.height]

    #     # Use ellipse equation to create grid masks
    #     strokeMask = ((gridX - ctrX) / axisA) ** 2 + ((gridY - ctrY) / axisB) **2 <= 1 + self.tolerance
    #     strokePts = np.argwhere(strokeMask)
    #     # Calculate fill mask based on stroke mask
    #     ptsX = strokePts[:,0]
    #     ptsY = strokePts[:,1]
    #     fillMask = ((ptsX - ctrX) / (axisA - self.stroke_weight)) ** 2 + ((ptsY - ctrY) / (axisB - self.stroke_weight)) ** 2 <= 1 + self.tolerance
    #     fillPts = strokePts[fillMask]
    #     # Flip coord order & convert to sets to remove 
    #     fillPts = set(map(tuple, fillPts))
    #     strokePts = set(map(tuple, strokePts)) - fillPts

    #     for (x_, y_) in strokePts: 
    #         canvas.SetPixel(x_, y_, *self.stroke_color)
    #     if self.do_fill: 
    #         for (x_, y_) in fillPts: 
    #             canvas.SetPixel(x_, y_, *self.fill_color)

class Line(PrimitiveComponent): 
    '''Draws a line.'''

    def __init__(self, startX: int, startY: int, endX: int, endY: int, 
                strokeColor: tuple, strokeWeight: int): 
        '''
        Parameters
        ------------
        x0: int
            x-coordinate of the start of the line
        y0: int
            y-coordinate of the start of the line
        x1: int
            x-coordinate of the end of the line
        y1: int
            y-coordinate of the end of the line
        strokeColor: tuple
            Color of the line, in (r,g,b) format
        strokeWeight: int
            Width of the line'''

        self.x0 = startX
        self.y0 = startY
        self.x1 = endX
        self.y1 = endY

        if not isinstance(strokeColor, tuple) or len(strokeColor) != 3:
            raise ValueError("Colors must be specified in tuples of length 3")
        for val in strokeColor:
            if val < 0 or val > 255:
                raise ValueError("Color values must be in [0,255]")
        self.stroke_color = strokeColor

        if strokeWeight < 1: 
            raise ValueError("Stroke weight cannot be less than 1")
        self.stroke_weight = strokeWeight

    def draw(self, canvas: FrameCanvas): 
        # Calculate slope
        try: 
            m = (self.y1 - self.y0) / (self.x1 - self.x0)
        except ZeroDivisionError: 
            # Draw vertical line
            for wt in range(self.stroke_weight): 
                wtFactor = wt * ((-1) ** wt)
                for y in range(max(0, self.y0), min(33, self.y1)): 
                    canvas.SetPixel(self.x0 + wtFactor, y, *self.stroke_color)
            return

        
        # Draw lines on alternating sides of original to increase width
        for wt in range(self.stroke_weight): 
            wtFactor = np.ceil(wt/2) * ((-1) ** wt)
            for x in range(max(0, self.x0), min(65, self.x1)): 
                canvas.SetPixel(x, np.trunc(m*x+self.y0+wtFactor), *self.stroke_color)

#endregion

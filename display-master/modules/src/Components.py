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

    def rotate(self, ptArray: Union[tuple, set, np.ndarray], degrees: int): 
        '''
        Helper method for rotating np.ndarray objects of 
        points
        ------------
        Parameters: 
        ------------
        ptArray: tuple(tuple(int, int)) 
                OR set(tuple(int, int)) 
                OR 2-D np.ndarray of int pairs
            - Array of point values 
        degrees: int
            - Degrees by which to rotate
        ------------
        Returns: array of points as set(tuple(int, int))
        ------------
        '''
        if degrees == 0: 
            return ptArray
        if isinstance(ptArray, tuple) or isinstance(ptArray, set): 
            points = np.array(ptArray)
        elif isinstance(ptArray, np.ndarray): 
            points = ptArray
        else: 
            raise ValueError("ptArray must be either tuple or np.ndarray!")

        rad = np.radians(degrees)
        translate_matrix = np.array([-self.x, -self.y])
        rotation_matrix = np.array([
            [np.cos(rad), -np.sin(rad)], 
            [np.sin(rad), np.cos(rad)]
        ])
        output = points + translate_matrix      # Translate to origin
        output = output @ rotation_matrix.T     # Rotate
        output = output - translate_matrix      # Translate back to original position
        output = np.round(output)       # Round result to nearest integers
        return set(map(tuple, output))
        # print(type(self.fill_pts))

        # if self.fill_pts: 
        #     self.fill_pts = self.fill_pts @ rotation_matrix.T
        # if self.stroke_pts: 
        #     self.stroke_pts = self.stroke_pts @ rotation_matrix.T

    @typechecked
    def __init__(self, x_: int, y_: int, w: int, h: int, 
                *, 
                fill: Union[tuple, None] = (255,255,255), 
                stroke: Union[tuple, None] = (255,255,255), 
                weight: int = 1,
                angle: int = 0):
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
        fill: tuple | None
            (r,g,b) value of fill color
        stroke: tuple
            (r,g,b) value of stroke color (applied *inside* specified width/height)
            If None: sets stroke_weight to 0
        weight: int
            Width of stroke in px (applied *inside* specified width/height)
        rotation: int
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

        for colorValue in (fill, stroke):
            if colorValue is not None: 
                if not isinstance(colorValue, tuple) or len(colorValue) != 3:
                    raise ValueError("Colors must be specified in tuples of length 3")
                for val in colorValue:
                    if val < 0 or val > 255:
                        raise ValueError("Color values must be in [0,255]")
        self.fill_color = fill
        self.stroke_color = stroke

        if self.stroke_color is None: 
            self.stroke_weight = 0
        else: 
            if weight < 0: 
                raise ValueError("Stroke weight cannot be negative")
            elif weight > self.height // 2: 
                raise ValueError(f"Stroke weight cannot be greater than half the height ({self.height//2})")
            self.stroke_weight = weight

        # Store coordinates of each point in shape
        self.rotation = angle
        self.getFillPts()
        self.getStrokePts()

        # Rotate shape if needed
        # self.rotation = angle       # Do we need to store rotation value?
        # if angle: 
        #     self.rotate(angle)

    def draw(self, canvas: FrameCanvas):
        # if not self.fill_pts and not self.no_fill: 
        #     self.getFillPts()
        # if not self.stroke_pts and self.stroke_weight > 0: 
        #     self.getStrokePts()

        if self.fill_color: 
            for pX, pY in self.fill_pts: 
                canvas.SetPixel(pX, pY, *self.fill_color)
        if self.stroke_color: 
            for pX, pY in self.stroke_pts: 
                canvas.SetPixel(pX, pY, *self.stroke_color)

class Rect(PrimitiveComponent): 
    '''Draws a rectangle.'''

    def getFillPts(self):
        # If do_fill is False, return empty
        if not self.fill_color: 
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
        pts_array = np.column_stack([xArr.ravel(), yArr.ravel()])
        # xArr, yArr = np.meshgrid(
        #     np.arange(fillX, fillX + fillW),
        #     np.arange(fillY, fillY + fillH)
        # )
        # Rotate points
        # xArr, yArr = self.rotate(pts_array, self.rotation)
        self.fill_pts = self.rotate(pts_array, self.rotation)
        # self.fill_pts = tuple(zip(xArr.ravel(), yArr.ravel()))

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
        horizPts = np.column_stack([hX.ravel(), hY.ravel()])
        # horizPts = tuple(zip(hX.ravel(), hY.ravel()))

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
        vertPts = np.column_stack([vX.ravel(), vY.ravel()])
        # vertPts = tuple(zip(vX.ravel(), vY.ravel()))

        # Concatenate horizontal & vertical
        # pts_array = np.concatenate(hPts, vPts)
        # xArr, yArr = self.rotate(horizPts + vertPts, self.rotation)
        self.stroke_pts = self.rotate(
            np.concatenate((horizPts, vertPts), axis=0), 
            self.rotation
            )
        # self.stroke_pts = tuple(zip(xArr.ravel(), yArr.ravel()))

        # Return concatenation of horizontal & vertical sides
        # self.stroke_pts = horizPts + vertPts

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
        # print(strokePts)
        strokePtsArray = np.array(list(strokePts))
        # Calculate fill mask based on stroke mask
        # ptsX, ptsY = zip(*strokePts)
        # print(strokePtsArray)
        # print(type(strokePtsArray))
        ptsX = strokePtsArray[:,0]
        ptsY = strokePtsArray[:,1]
        # ptsX = np.array(ptsX)
        # ptsY = np.array(ptsY)
        fillMask = ((ptsX - ctrX) / (axisA - self.stroke_weight)) ** 2 + ((ptsY - ctrY) / (axisB - self.stroke_weight)) ** 2 <= 1 + self.tolerance
        fillPts = strokePtsArray[fillMask]
        # Rotate shape
        strokePts = self.rotate(strokePts, self.rotation)
        fillPts = self.rotate(fillPts, self.rotation)
        # Convert coords to sets of tuples
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
                stroke: tuple = (255, 255, 255), 
                *, 
                weight: int = 1): 
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
        stroke: tuple
            Color of the line, in (r,g,b) format
        weight: int
            Width of the line'''

        self.x0 = startX
        self.y0 = startY
        self.x1 = endX
        self.y1 = endY

        if not isinstance(stroke, tuple) or len(stroke) != 3:
            raise ValueError("Colors must be specified in tuples of length 3")
        for val in stroke:
            if val < 0 or val > 255:
                raise ValueError("Color values must be in [0,255]")
        self.stroke_color = stroke

        if weight < 1: 
            raise ValueError("Stroke weight cannot be less than 1")
        self.stroke_weight = weight

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

#region text components
class Text(Component):
    '''Draws text to the display'''


#endregion
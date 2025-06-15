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

# Clock component
from datetime import datetime as dt
from datetime import tzinfo
import pytz

class Component:
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
        
    @typechecked
    def __init__(self, x_: int, y_: int, w: int, h: int, 
                *, 
                fill: [tuple, None] = (255,255,255), 
                stroke: Optional[tuple] = None, 
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

    def draw(self, canvas: FrameCanvas):
        if self.fill_color: 
            for pX, pY in self.fill_pts: 
                canvas.SetPixel(pX, pY, *self.fill_color)
        if self.stroke_color: 
            for pX, pY in self.stroke_pts: 
                canvas.SetPixel(pX, pY, *self.stroke_color)

class Rect(PrimitiveComponent): 
    '''Draws a rectangle.'''

    def getFillPts(self):
        # If fill_color is False, return empty
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
        self.fill_pts = self.rotate(pts_array, self.rotation)

    def getStrokePts(self): 
        # If stroke_color is False, return empty
        if not self.stroke_color: 
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

        # Concatenate horizontal & vertical
        self.stroke_pts = self.rotate(
            np.concatenate((horizPts, vertPts), axis=0), 
            self.rotation
            )

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
        ptsX = strokePtsArray[:,0]
        ptsY = strokePtsArray[:,1]
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

class RightTriangle(PrimitiveComponent): 
    '''Draw a right triangle with the right angle in the bottom-left'''
    
    tolerance = 0

    def getFillPts(self): 
        # If fill_color is False, return empty
        if not self.fill_color: 
            self.fill_pts = ()
            return

        # Create Numpy grid to match matrix
        # Get canvas width & height from environment vars
        # Subtract 1 to account for indexing at 0
        canvasH = int(os.getenv("MATRIX_ROWS", 32)) - 1
        canvasW = int(os.getenv("MATRIX_COLS", 32)) - 1
        gridX, gridY = np.ogrid[:canvasW, :canvasH]

        slope = self.height / self.width

        # Trim value
        TOLERANCE = -0.99

        fillMaskHypotenuse = gridY - slope * gridX >= self.stroke_weight + TOLERANCE
        fillMaskLeft = gridX >= self.stroke_weight
        fillMaskBottom = gridY <= self.height - self.stroke_weight
        fillPts = np.argwhere(fillMaskHypotenuse & fillMaskLeft & fillMaskBottom)
        # Translate mask to shape position
        fillPts += np.array([self.x, self.y])
        # fillPtsArray = np.array(list(fillPts))
        self.fill_pts = self.rotate(fillPts, self.rotation)
        
    def getStrokePts(self): 
        # If stroke_color is False, return empty
        if not self.stroke_color: 
            self.stroke_pts = ()
            return

        # Create Numpy grid to match matrix
        # Get canvas width & height from environment vars
        # Subtract 1 to account for indexing at 0
        canvasH = int(os.getenv("MATRIX_ROWS", 32)) - 1
        canvasW = int(os.getenv("MATRIX_COLS", 32)) - 1
        gridX, gridY = np.ogrid[:canvasW, :canvasH]

        slope = self.height / self.width

        # Trim values to make things work right
        OUTER_SHIFT = self.stroke_weight - 1
        TOLERANCE = 0.5

        strokeMaskOuter = (gridY - slope * gridX > -self.stroke_weight + OUTER_SHIFT)
        strokeMaskHypotenuse = strokeMaskOuter & \
            (gridY - slope * gridX <= 0 + OUTER_SHIFT + TOLERANCE) & \
            (gridY >= 0) & (gridY <= self.height)
        strokeMaskLeft = (gridX >= 0) & \
            (gridX < self.stroke_weight) & \
            (gridY <= self.height) & \
            strokeMaskOuter
            # (gridY >= 0)
        strokeMaskBottom = (gridY <= self.height) & \
            (gridY > self.height - self.stroke_weight) & \
            (gridX >= 0) & \
            strokeMaskOuter
            # (gridX <= self.width)
        strokePts = np.argwhere(strokeMaskHypotenuse | strokeMaskLeft | strokeMaskBottom)
        # Translate mask to shape position
        strokePts += np.array([self.x, self.y])
        self.stroke_pts = self.rotate(strokePts, self.rotation)



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

    def adjustAlignment(self): 
        if self.right_aligned: 
            # Compute length of string when printed
            totalLen = 0
            for c in self.text: 
                totalLen += self.font.CharacterWidth(ord(c))
            self.x = self.x_og - totalLen        

    @typechecked
    def __init__(
        self, x_: int, y_: int, text_: str, 
        *, 
        font: str = "basic/4x6.bdf",
        color: tuple = (255, 255, 255),
        rightAlign: bool = False,
        ):
        '''
        Parameters
        ------------
        x_: int
            x position (left-hand side)
        y_: int
            y position
            N.B. position of TEXT BASELINE
        text_: str
            Text to be drawn
        font: str
            Path to font to use
        color: tuple
            Color of text
        rightAlign: bool
            Whether to align text to right
        '''
        super().__init__(x_, y_)
        self.x_og = x_      # Store original x value to allow right-aligning
        self.text = text_
        if not font.endswith(".bdf"): 
            raise ValueError("Font must be a .bdf file")
        self.font_path = FONTS_PATH + font       # Do we need this?
        if not os.path.exists(self.font_path):
            raise ValueError("Font path does not exist")
        self.font = graphics.Font()
        self.font.LoadFont(FONTS_PATH + font)
        self.font_color = graphics.Color(*color)
        self.right_aligned = rightAlign
        self.adjustAlignment()

    def draw(self, canvas: FrameCanvas): 
        return graphics.DrawText(canvas, self.font, self.x, self.y, self.font_color, self.text)

class ScrollingText(Text):
    '''Draws text to the display'''

    # Define scrolling modes
    ONCE = 0
    LOOP = 1
    BOUNCE = 2

    @typechecked
    def __init__(
        self, x_: int, y_: int, text_: str, 
        *, 
        font: str = "basic/4x6.bdf",
        color: tuple = (255, 255, 255),
        speed: float = -1,
        mode: int = ONCE,
        delay: int = 0, 
        spacing: int = 0
        ):
        '''
        Parameters
        ------------
        x_: int
            x position (left-hand side)
        y_: int
            y position
            N.B. position of TEXT BASELINE
        text_: str
            Text to be drawn
        font: str
            Path to font to use
        color: tuple
            Color of text
        speed: float
            Rate of scrolling (px/frame update)
            Defaults to -1 (text moves 1 px left per frame)
        mode: int
            Scroll mode
            Must be ONCE, LOOP, or BOUNCE
            N.B. LOOP mode only works if text is longer than bounding box
        delay: int
            No. of frame updates to wait between scrolling iterations
            ONCE & LOOP modes: scrolls around once, then pauses at original position
            BOUNCE mode: pauses at each end of text before changing direction
        spacing: int
            No. of px space between iterations in LOOP mode
            Has no effect in ONCE or BOUNCE modes
        ----------------
        Other Attributes
        ----------------
        scroll_index: int
            Number of frame updates executed (multiplied by rate to calculate new x-pos)
        length: int
            Length of string (in px) when printed
            Updated on initial draw
        direction_mult: int
            Rate multiplier to change direction of scrolling (for BOUNCE mode)
        '''
        super().__init__(x_, y_, text_, font=font, color=color)
        self.rate = speed
        if mode not in [self.ONCE, self.LOOP, self.BOUNCE]:
            raise ValueError("Scrolling mode must be ScrollingText.ONCE, ScrollingText.LOOP, or ScrollingText.BOUNCE")
        self.mode = mode
        self.delay = delay
        self.spacing = spacing
        self.scroll_index = 0
        self.delay_count = 0
        self.direction_mult = 1

    def draw(self, canvas: FrameCanvas): 
        self.length = super().draw(canvas)
        self.scroll_index += 1
        return self.length

    def loop(self, canvas: FrameCanvas): 
        # Ignore rest of function if scroll rate is 0
        if self.rate == 0: 
            self.draw(canvas)
            return
        
        newPos = self.x + self.rate * self.scroll_index

        # Check for active delay
        if (
            (self.scroll_index == 0
            or self.mode == self.BOUNCE and newPos + self.length <= canvas.width)
            and self.delay_count < self.delay
            ): 
            self.delay_count += 1
            graphics.DrawText(
                canvas, self.font, 
                newPos, 
                self.y, self.font_color, self.text
            )
            return

        else: 
            self.delay_count = 0

        # Test position; reset/change direction if needed
        # ONCE mode
        if self.mode == self.ONCE:
            # Test whether text has left display
            if (
                (self.rate < 0 and newPos + self.length < 0) # If a bounding box is used, set last value to self.x instead of 0!
                or (self.rate > 0 and newPos > canvas.width)
            ):
                # Set scroll index to far end of display
                self.scroll_index = canvas.width / self.rate

        # LOOP mode
        elif self.mode == self.LOOP:
            # Test whether *second string* has returned to original position
            if (
                (self.rate < 0 and newPos + (self.length + self.spacing) < 0)
                or (self.rate > 0 and newPos - (self.length + self.spacing)  > 0)
            ):
                # Reset scroll index
                # Add self.direction_mult to cancel out increment at end of function call
                # self.scroll_index = 0 + self.direction_mult
                self.scroll_index = 0
                self.draw(canvas)
                return

        # BOUNCE mode
        else:  
            # Test whether text has reached extreme end of display
            direction = self.rate * self.direction_mult
            if (
                (direction < 0 and newPos + self.length < canvas.width)
                or (direction > 0 and newPos > self.x)  # Left bounce limit: self.x
            ):
                # Change direction
                self.direction_mult *= -1

        graphics.DrawText(
            canvas, self.font, 
            newPos, 
            self.y, self.font_color, self.text
            )
        # If mode is LOOP, draw second string (to avoid blank space) after 
        # (later in scroll pattern) original string
        if self.mode == self.LOOP: 
            graphics.DrawText(
                canvas, self.font, 
                newPos - (self.length + self.spacing) * np.sign(self.rate), # Multiply by sign of rate to ensure proper placement
                self.y, self.font_color, self.text
                )

        # Multiply increment by direction_mult to allow bouncing
        self.scroll_index += 1 * self.direction_mult
        

#endregion

#region image components
class Icon(Component): 
    '''Draw a .bmp image directly to matrix'''

    @typechecked
    def __init__(self, x_: int, y_: int, path: str):
        '''
        Parameters: 
        -------------
        x_: int
            x position
        y_: int
            y position
        path: str
            Path of .bmp file to use
            N.B. must be in .bmp format
        '''

        super().__init__(x_, y_)
        if not os.path.exists(path): 
            raise ValueError("Path does not exist!")
        elif not path.endswith(".bmp"): 
            raise ValueError("Path must be an image in .bmp format")
        self.path = path        # Do we need to store this?
        imgTemp = Image.open(path)
        self.img = imgTemp.convert("RGB")
    
    def draw(self, canvas: FrameCanvas):
        canvas.SetImage(self.img, self.x, self.y)
    
class RasterImage(Icon): 
    '''Scale, then draw an image to matrix'''

    @typechecked
    def __init__(self, x_: int, y_: int, 
        path: str, 
        *,
        width: Optional[int], height: Optional[int],
        antialias: bool = True):
        '''
        Parameters: 
        -------------
        x_: int
            x position
        y_: int
            y position
        path: str
            Path of image file to use
        width: int
            Bound on image width (maintains aspect ratio)
        height: int
            Bound on image height (maintains aspect ratio)
        antialias: bool
            Flag to optionally disable anti-aliasing
        '''

        self.x = x_
        self.y = y_

        if not os.path.exists(path): 
            raise ValueError("Path does not exist!")
        elif os.path.splitext(path)[-1] not in [".png", ".jpg", ".bmp"]: 
            raise ValueError("Path must be an image in .png, .jpg, or .bmp format")
        self.path = path        # Do we need to store this?
        imgTransform = Image.open(path)
        # Get image dimensions as fallback value for image bound
        imgW, imgH = imgTransform.size
        thumbnailSize = (width or imgW, height or imgH)     # Use imgW, imgH if width, height are None (respectively)
        if antialias: 
            imgTransform.thumbnail(thumbnailSize, Image.ANTIALIAS)
        else: 
            imgTransform.thumbnail(thumbnailSize)
        self.img = imgTransform.convert("RGB")

#endregion

#region complex components
class DateTimeDisplay(Text): 
    '''A simple clock or date (or both) display'''        

    @typechecked
    def __init__(
        self, x_: int, y_: int,
        *, 
        font: str = "basic/4x6.bdf",
        color: tuple = (255, 255, 255),
        rightAlign: bool = True,
        dtFormat: str = "%-I:%M",
        timezone: tzinfo = pytz.timezone("US/Eastern"),
        ):
        '''
        Parameters
        ------------
        x_: int
            x position (left-hand side)
        y_: int
            y position
            N.B. position of TEXT BASELINE
        text_: str
            Text to be drawn
        font: str
            Path to font to use
        color: tuple
            Color of text
        rightAlign: bool
            Text aligns to right if True
        dtFormat: str
            Format of datetime string to print out
        timezone: tzinfo
            Timezone object specifying timezone to show
            Uses pytz library
        -----------------
        Other Attributes
        -----------------
        zero_width: int
            Width of zero character in px
            Used to adjust for # of zero characters removed
        '''
        initText = dt.now(tz=timezone).strftime(dtFormat)
        super().__init__(x_, y_, initText, font=font, color=color, rightAlign=rightAlign)
        self.format = dtFormat
        self.tz = timezone


    def loop(self, canvas: FrameCanvas): 
        # Update text
        now = dt.now(tz=self.tz)
        self.text = now.strftime(self.format)
        self.adjustAlignment()
        self.draw(canvas)

class TickerText(ScrollingText):
    '''A scrolling text box that displays multiple messages'''

    @typechecked
    def __init__(
        self, x_: int, y_: int, messages_: Union[list, tuple, set], 
        *, 
        font: str = "basic/4x6.bdf",
        color: tuple = (255, 255, 255),
        speed: float = -1,
        spacing: int = 0, 
        wrap: bool = True
        ):
        '''
        Parameters
        ------------
        x_: int
            x position (left-hand side)
        y_: int
            y position
            N.B. position of TEXT BASELINE
        text_: str
            Text to be drawn
        font: str
            Path to font to use
        color: tuple
            Color of text
        speed: float
            Rate of scrolling (px/frame update)
            Defaults to -1 (text moves 1 px left per frame)
        spacing: int
            No. of px space between iterations in LOOP mode
            Has no effect in ONCE or BOUNCE modes
        ----------------
        Other Attributes
        ----------------
        msg_index: int
            Index of message currently being printed
        msg_x: list(int)
            x-position of each message string, updated individually at runtime
        msg_len: list(int)
            Lengths of each message
            Updated as messages are printed
        next_msg_len: int
            Length of next message printed
            Used to test when to print next message
        update_msg_idx: list(int)
            List of message indices to update at each frame update
            Indices are added to or removed from this list at every frame update as
            they enter or leave the display
        '''
        for m in messages_: 
            if not isinstance(m, str): 
                raise ValueError("Messages must be strings!")

        super().__init__(x_, y_, messages_[0], font=font, color=color,
            speed=speed, spacing=spacing)
        self.wrap = wrap
        self.messages = messages_
        self.msg_index = 0
        self.msg_x = [0] * len(messages_)
        self.msg_len = [0] * len(messages_)
        # self.update_msg_idx = [0]
        self.first_idx = 0
        self.last_idx = 0

    def draw(self, canvas: FrameCanvas): 
        self.msg_len[0] = super().draw(canvas)
        self.msg_x[0] += self.rate
        self.msg_x[1] = self.msg_x[0] + self.msg_len[0] + self.spacing
        # self.update_msg_idx = [0, 1]
        return self.msg_len[0]

    def loop(self, canvas: FrameCanvas): 
        # Ignore rest of function if scroll rate is 0
        if self.rate == 0: 
            self.draw(canvas)
            return
        
        # Test whether next message needs to be displayed
        if (
            (
                self.rate < 0 
                and self.msg_x[self.last_idx] + self.msg_len[self.last_idx] < canvas.width - self.spacing
            ) or (
                self.rate > 0 and self.msg_x[self.last_idx] > self.spacing
            )
        ): 
            # If next message needs to be printed, print first, then add to focus list
            nextMsg = self.last_idx + 1
            if nextMsg >= len(self.messages): 
                nextMsg = 0
            self.msg_x[nextMsg] = self.msg_x[self.last_idx] + self.msg_len[self.last_idx] + self.spacing
            # self.msg_len[nextMsg] = graphics.DrawText(
            #     canvas, self.font, 
            #     self.msg_x[nextMsg], 
            #     self.y, self.font_color, self.messages[nextMsg]
            # )
            # self.msg_x[nextMsg] += self.rate
            self.last_idx = nextMsg

        # Test whether first msg is still in frame
        if (
            (self.rate < 0 and self.msg_x[self.first_idx] + self.msg_len[self.first_idx] < 0) # If a bounding box is used, set last value to self.x instead of 0!
            or (self.rate > 0 and self.msg_x[self.first_idx] > canvas.width)
        ):
            # If message has left frame, stop drawing and remove from update_msg_idx
            self.first_idx += 1
            if self.first_idx >= len(self.messages): 
                self.first_idx = 0

        # Draw messages

        idx = self.first_idx        # Loop index

        # Define check value for last index to allow looping 
        # around to beginning of messages
        lastIdxCheckVal = self.last_idx + 1    # If last_idx does not wrap, check val = last_idx
        if self.last_idx < self.first_idx:  # If last_idx does wrap, add first_idx
            lastIdxCheckVal += self.first_idx  
            if self.wrap: 
                lastIdxCheckVal += 1        # Add 1 to avoid wraparound-to-zero corner case

        while idx < lastIdxCheckVal:
            # Wrap idx value around to match message indices
            idxMod = idx % len(self.messages)

            self.msg_len[idxMod] = graphics.DrawText(
                canvas, self.font, 
                self.msg_x[idxMod], 
                self.y, self.font_color, self.messages[idxMod]
                )
            self.msg_x[idxMod] += self.rate
            idx += 1

        # Update index list
        # self.update_msg_idx = [i for i in self.update_msg_idx if i not in idxToRemove]
        # self.update_msg_idx.extend(idxToAdd)
        

#endregion
#!/bin/python
'''Boilerplate code for creating new matrix layouts'''

# Import config module
import sys
sys.path.insert(0, "../..")

import config
from config import FONTS_PATH

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Element dependencies
from PIL import Image

# Load matrix from .env values
matrix = config.matrix_from_env()

def main():
    # Create canvas for caching next frame
    canvas = matrix.CreateFrameCanvas()

    # Draw elements

    # TextElement 'me'
    #   Text: Ta'bu e tay!
    #   Font: basic/5x7.bdf
    #   Color: goldenrod
    #   Pos: [2, 8]
    myFont = graphics.Font()
    myFont.LoadFont('../../../fonts/basic/5x7.bdf')
    graphics.DrawText(canvas,
        myFont,
        2, 8,
        graphics.Color(*[218, 165, 32]),
        "Ta'bu e tay!")

    # IconElement 'sun'
    #   Path: ../weather/sunny.bmp
    #   Pos: [20, 10]
    img = Image.open('../weather/sunny.bmp')
    img = img.convert('RGB')
    canvas.SetImage(img, 20, 10)

    canvas = matrix.SwapOnVSync(canvas)

if __name__ == '__main__':
    main()
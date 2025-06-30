#!/bin/python
'''
Module class definition
Version 1.0
Jacob Schuetter

Template for other module definitions
'''

# Default delay value, in seconds
DEFAULT_DELAY = 1/24

class Module: 
    '''Template for other module definitions'''

    def __init__(self, matrix, canvas, *, doLoop = False, delay = DEFAULT_DELAY): 
        '''
        Parameters
        -----------
        matrix: rgbmatrix.RGBMatrix
        canvas: rgbmatrix.FrameCanvas
        do_loop: bool
            Whether module has frame updates
        delay: float
            Number of seconds (usually a fraction) to delay between
            frame updates
        '''
        self.matrix = matrix
        self.canvas = canvas
        self.do_loop = doLoop
        self.delay = delay
        self.components = []

    def draw(self): 
        '''Code to run on initial matrix draw'''
        self.canvas.Clear()
        for c in self.components: 
            c.draw(self.canvas)
        self.matrix.SwapOnVSync(self.canvas)

    def update(self): 
        '''Optional method for updating module data (e.g. fetching from API)'''
        return
    
    def loop(self): 
        '''Code to run on every subsequent frame update'''
        self.update()
        self.draw()

    def buffer_canvas(self):
        '''Prep next canvas without updating matrix'''
        self.canvas.Clear()
        for c in self.components: 
            c.draw(self.canvas)

    def publish_canvas(self):
        '''Publish canvas in current state to the matrix display.'''
        self.matrix.SwapOnVSync(self.canvas)
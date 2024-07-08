#!/bin/python
# Insert project root directory into sys.path
import sys
sys.path.insert(0, "../..")

# RGB Matrix dependencies
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config 
from config import FONTS_PATH

# CLI dependencies
import cmd
from modules.src import Elements
# from modules.src.Elements import IconElement
import os, json
from re import escape
import logging
from ast import literal_eval
import argparse

log = logging.getLogger(__name__)

# Standard path to store JSON files at
SRC_PATH = "./srcFiles"
# Global variable containing current working data (read in from JSON or created from CLI)
# Contains comp name, comp json path, list of Element objects, dict of Element names & data
working = {}
matrix = config.matrix_from_env()
canvas = matrix.CreateFrameCanvas()

ELEMENT_TYPES = {"icon": Elements.IconElement, 
        "image":None, 
        "text":None, 
        "rect":None, 
        "ellipse":None
        }

class ModuleEditor(cmd.Cmd):
    intro = "Welcome to Jaybird's rgbmatrix Module Editor. Type help or ? to list commands.\n"
    prompt = "(ModuleEditor): "
    file = None

    def do_new(self, line):
        '''Create new matrix composition

        name: str
            Name of composition (for JSON storage)
        parentDir: str -- NOT IN USE
            Path of parent directory for JSON storage file
        '''

        global working

        # (name, parentDir) = (parse(line), SRC_PATH)
        # Temporary override
        # Need to figure out how to allow passing (parsing) optional parameters in CLI
        if not line: 
            print("Must provide composition name!")
            return

        (name,) = parse(line)
        parentDir = SRC_PATH
        # 
        if not os.path.isdir(parentDir): 
            os.mkdir(parentDir)

        working = {}
        working["name"] = name
        working["path"] = os.path.join(parentDir,name + ".json")
        working["elements"] = []
        working["json"] = {} 

    def do_open(self, line):
        '''Open matrix composition JSON file

        path: str
            Path of JSON file to open
        '''

        global working
        path = os.path.join(SRC_PATH, "tempName.json")
        with open(path, "wr") as file:
            working["path"] = path
            working["json"] = json.load(file.read())
            working["elements"] = json_get_elements(working["json"])

    def do_close(self):
        'Close current working composition'
        global working, workingName, workingPath
        write_json()
        working = {}

    def do_add(self, line):
        '''Add new element to current composition

        Usage: add [elType] [elArgs]

        elType: str
            Type of element to create
            See modules/src/Elements.py for element class definitions
        elArgs: *str
            Arguments for element constructor (space-delimited)
            See Element classes for details
        '''

        global working
        # Check for open composition
        if not working: 
            print("Must have open composition! \nUse `new` to create a comp or `open` to import one from JSON.")
            return
        # elType = "IconElement"
        log.debug(line)
        # if line == "" or line == " ":
        #     print("Select an element type to add:\n" + str(list(ELEMENT_TYPES.keys())))
        #     return
        # try: 
        args = parse(line)
        # Input validation
        if len(args) < 1 or args[0] not in ELEMENT_TYPES.keys():
            # Validate element type
            print("Select an element type to add:\n" + str(list(ELEMENT_TYPES.keys())))
            return
        # elif len(args) < 2 or type(args[1]) is not str:
        #     # Validate element name
        #     print("Must provide valid element name!")
        #     return

        print(args)
        elType = args[0]
        elArgs = args[1:]
        # (elType, elName, *elArgs) = args
        # If all arguments are valid, test arguments
        invalidArgs = ELEMENT_TYPES[elType].testArgs(*elArgs)
        if invalidArgs:
            print(invalidArgs)
            print("Usage: " + ELEMENT_TYPES[elType].__name__)
            print(ELEMENT_TYPES[elType].params)
            return
        
        newEl = ELEMENT_TYPES[elType](*elArgs)
        # except ValueError as ve:
        #     log.debug(ve)
        #     # Test each argument for validity
        #     # If supplied element type is invalid, print valid types
        #     if len(args) < 1 or args[0] not in ELEMENT_TYPES.keys():
        #         print("Select an element type to add:\n" + str(list(ELEMENT_TYPES.keys())))
        #     elif len(args) < 2 or type(args[1]) is not str:
        #         print("Must provide valid element name!")
        #     else:
        #         # If all args are (apparently) valid, re-raise exception
        #         raise
        #         ELEMENT_TYPES[args[0]].print_docs()
        #     return
        # newEl = ELEMENT_TYPES[elType](elName, "../weather/sunny.bmp", (0,0))

        working["elements"].append(newEl)
        newEl.draw(canvas)
        matrix.SwapOnVSync(canvas)

        # Create sub-dict for element class if not existing
        if working["json"].get(elType) is None:
            working["json"][elType] = {}
        working["json"][elType][newEl.name] = newEl.__dict__
        # write_json()

    def do_exit(self, line):
        'Exit ModuleEditor CLI'
        print("Closing ModuleEditor...")
        self.do_close()
        canvas.Clear()
        matrix.SwapOnVSync(canvas)
        return True

def parse(line: str) -> tuple:
    'Convert space-delimited arguments to tuple of strings'
    args = tuple(line.split())
    log.debug(args)
    return args

def new_json():
    '''Generates fresh JSON template

    Creates sub-dict for each class name in ELEMENT_TYPES
    '''
    outDict = {}
    for t in ELEMENT_TYPES:
        outDict[t] = {}
    return outDict

def write_json():
    'Write changes to JSON file'
    global working
    with open(working["path"], "w") as file:
        json.dump(working["json"], file)

def json_get_elements(src: dict):
    pass

if __name__ == "__main__":
   ModuleEditor().cmdloop() 


# # Load matrix from .env values
# matrix = config.matrix_from_env()
# 
# # Load fonts
# timeFont = graphics.Font()
# timeFont.LoadFont(FONTS_PATH+"basic/7x13B.bdf")
# dateFont = graphics.Font()
# dateFont.LoadFont(FONTS_PATH+"basic/5x7.bdf")
# fontColor = graphics.Color(255, 255, 255)
# 
# def main():
#     # Create canvas for caching next frame
#     nextCanvas = matrix.CreateFrameCanvas()
# 
#     # Continuously update clock
#     while True:
#         nextCanvas.Clear()
#         now = dt.datetime.now(tz=TZ_EST)
#         # Draw date text, then time
#         graphics.DrawText(nextCanvas, dateFont, DATE_X, DATE_Y, fontColor, 
#                 now.strftime(DATE_FORMAT))
#         if MILITARY_TIME:
#             graphics.DrawText(nextCanvas, timeFont, TIME_X, TIME_Y, fontColor, 
#                 now.strftime(TIME_FORMAT_24))
#         else:
#             graphics.DrawText(nextCanvas, timeFont, TIME_X-1, TIME_Y, fontColor, 
#                 now.strftime(TIME_FORMAT_12))
#         nextCanvas = matrix.SwapOnVSync(nextCanvas)
#         time.sleep(1)
# 
# if __name__=="__main__":
#     main()

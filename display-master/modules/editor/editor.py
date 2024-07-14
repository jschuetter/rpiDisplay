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
from typing import Any

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

        Usage: new [compName] [parentDir - WIP]

        compName: str
            Name of composition (for JSON storage)
        parentDir: str -- NOT IN USE
            Path of parent directory for JSON storage file
        '''

        global working

        # (name, parentDir) = (parse(line), SRC_PATH)
        # Temporary override
        # Need to figure out how to allow passing (parsing) optional parameters in CLI
        (compName,) = parse(line)
        parentDir = SRC_PATH
        # 
        if not os.path.isdir(parentDir): 
            os.mkdir(parentDir)

        working = {}
        working["name"] = compName
        working["path"] = os.path.join(parentDir,compName + ".json")
        if os.path.exists(working["path"]): 
            while True:
                confirm = input("This path already exists! Do you want to over[w]rite, \
                                [o]pen, or [c]ancel? (w/o/c)")
                confirm = confirm.partition(" ")[0].lower()
                if confirm == "w": break
                elif confirm == "o": self.do_open(compName)
                elif confirm == "c": 
                    working = {}
                    print("Canceled creating composition.")
                    return
                else: 
                    print("Invalid response.")
        working["elements"] = []
        working["json"] = {} 

    def do_open(self, line):
        '''Open matrix composition JSON file

        Usage: open [path]

        path: str
            Path of JSON file to open
        '''

        global working
        args = parse(line)
        if not os.path.isfile(args[0]) or not args[0].endswith(".json"):
            print("First argument must be valid JSON file")
            return
        else: 
            path = args[0]
        
        # path = os.path.join(SRC_PATH, "tempName.json")
        print(path)
        with open(path) as file:
            working["path"] = path
            working["json"] = json.load(file)
            #Populate element list -- iterate over classes, then objects
            working["elements"] = []
            for k, v in working["json"].items():
                for props in v:
                    newEl = ELEMENT_TYPES[k].from_dict(props)
                    newEl.draw(canvas)
                    # print(newEl.__dict__)
                    working["elements"].append(newEl)
            matrix.SwapOnVSync(canvas)
            # working["elements"] = []

    def do_close(self, line):
        'Close current working composition'
        global working
        if not working:
            # Directly return if no composition is open
            return
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
        
        log.debug(line)
        args = parse(line)
        # Input validation
        if len(args) < 1 or args[0] not in ELEMENT_TYPES.keys():
            # Validate element type
            print("Select an element type to add:\n" + str(list(ELEMENT_TYPES.keys())))
            return

        elType = args[0]
        elArgs = args[1:]
        invalidArgs = ELEMENT_TYPES[elType].testArgs(*elArgs)
        if invalidArgs:
            print(invalidArgs)
            print(ELEMENT_TYPES[elType].docstr)
            return
        if elArgs[0] in [el.name for el in working["elements"]]:
            print("Name must be unique (all other args valid).")
            return
        newEl = ELEMENT_TYPES[elType](*elArgs)

        working["elements"].append(newEl)
        newEl.draw(canvas)
        matrix.SwapOnVSync(canvas)

        # Create sub-dict for element class if not existing
        if working["json"].get(elType) is None:
            working["json"][elType] = []
        working["json"][elType].append(newEl.__dict__)
        print(working["json"])
        write_json()

    def do_ls(self, line):
        '''Print list of elements in current directory
        
        Usage: ls [dir - WIP]
        
        dir: str
            Name of directory to print
            Prints objects in directory or, if dir is name of object
            in current working directory, prints object properties'''
        
        global working
        if not working: 
            print("No open composition")
            return

        args = parse(line)

        if not args: 
            print(*[el.name.value for el in working["elements"]], sep="\t\t")
            return
        else: 
            for el in working["elements"]:
                if el.name.value == args[0]:
                    print_props(el)
                    return
        print("Object not found.\n")
        print(self.do_ls.__doc__)
        return

    def do_exit(self, line):
        'Exit ModuleEditor CLI'
        print("Closing ModuleEditor...")
        self.do_close(None)
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
        json.dump(working["json"], file, cls=Elements.CEnc)

def print_props(obj: Any):
    '''Print all object properties and their values in formatted output
    
    obj: Any
        Object to print'''
    
    for k, v in obj.__dict__.items():
        if isinstance(v, Elements.Property):
            print(f"{k}: {v.value}")
        else: 
            print(f"{k}: {v}")

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

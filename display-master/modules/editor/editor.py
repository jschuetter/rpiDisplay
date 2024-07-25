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
from warnings import warn
import re
from shutil import copy as fcopy
from copy import deepcopy

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
ELEMENT_CLASS_NAMES = { class_:name_ for name_, class_ in ELEMENT_TYPES.items()}

class ModuleEditor(cmd.Cmd):
    intro = "Welcome to Jaybird's rgbmatrix Module Editor. Type help or ? to list commands.\n"
    prompt = "(ModuleEditor): "
    file = None

    def do_new(self, line):
        '''Create new matrix composition

        Usage: new [compName]

        compName: str
            Name of composition (for JSON storage)
        '''

        global working

        parentDir = SRC_PATH
        if not os.path.isdir(parentDir): 
            os.mkdir(parentDir)

        (compName,) = parse(line)
        if not re.match("^[A-Za-z0-9_]*$", compName):
            print("Invalid name.")
            print("Comp names must only contain alphanumeric characters and underscores.")
            return

        working = {}
        path_ = os.path.join(parentDir,compName + ".json")
        if os.path.exists(path_): 
            while True:
                confirm = input("This path already exists! Do you want to over[w]rite, \
                                [o]pen, or [c]ancel? (w/o/c)")
                confirm = confirm.partition(" ")[0].lower()
                if confirm in ["w", "overwrite", "write"]: 
                    break
                elif confirm in ["o", "open"]: 
                    self.do_open(compName)
                    break
                elif confirm in ["c", "cancel"]: 
                    working = {}
                    print("Canceled creating composition.")
                    return
                else: 
                    print("Invalid response.")
        # Set comp properties
        working["name"] = compName
        working["path"] = path_
        working["elements"] = []

    def do_open(self, line):
        '''Open matrix composition JSON file

        Usage: open [comp]

        comp: str
            Name of JSON file to open
        '''

        global working, canvas, matrix

        args = parse(line)

        if not args: 
            # Print docs if no arguments given
            print(self.do_open.__doc__)
            return

        if working: 
            while True:
                confirm = input("There is already an open composition. "
                    "Do you want to close it and open a new one? (y/n)")
                confirm = confirm.partition(" ")[0].lower()
                if confirm in ["n", "no"]:
                    # Cancel, do nothing
                    print("Canceling...")
                    return
                elif confirm in ["y", "yes"]:
                    # Close open comp and continue with open
                    self.do_close("")
                    break
                # Else, get repeat confirmation request

        path = os.path.join(SRC_PATH, args[0] + ".json")
        print(path)
        if not os.path.isfile(path):
            print("First argument must be valid composition name")
            print("Use `ls` to see existing comps or `new` to create a comp")
            return
        
        # path = os.path.join(SRC_PATH, "tempName.json")
        print(path)
        with open(path) as file:
            working["path"] = path
            jsonFile = json.load(file)
            #Populate element list -- iterate over classes, then objects
            working["elements"] = []
            for k, v in jsonFile.items():
                for props in v:
                    newEl = ELEMENT_TYPES[k].from_dict(props)
                    # print(newEl.__dict__)
                    working["elements"].append(newEl)
            refresh_canvas()

    def complete_open(self, text, line, begidx, endidx):
        # print(f"args: {text}, {line}, {begidx}, {endidx}")
        # Ignore after 1st argument
        if len(line.split()) + line.endswith(" ") > 2: 
            return []
        
        valid = [os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)]
        return [v for v in valid if v.startswith(text)]

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

        global working, matrix
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
        refresh_canvas()
        write_json()

    def complete_add(self, text, line, begidx, endidx):
        # Ignore completion after first argument
        if len(line.split()) + line.endswith(" ") > 2: 
            return []

        valid = list(ELEMENT_TYPES.keys())
        return [s for s in valid if s.startswith(text)]

    def do_ls(self, line):
        '''Print list of elements in current directory
        
        Usage: ls [dir - WIP]
        
        dir: str
            Name of directory to print
            Prints objects in directory or, if dir is name of object
            in current working directory, prints object properties'''
        
        global working

        args = parse(line)

        if not args: 
            if not working: 
                # If no open comp, print composition files
                print(*[os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)], sep="\t\t")
            else: 
                print(*[el.name.value for el in working["elements"]], sep="\t\t")
            return
        else: 
            for el in working["elements"]:
                if el.name.value == args[0]:
                    print_props(el)
                    return
        print("Object not found.\n")
        self.do_help("ls")
        return

    def complete_ls(self, text, line, begidx, endidx):
        # Ignore after 1st argument
        if not working or (len(line.split()) + line.endswith(" ") > 2):
            return []

        valid = [el.name.value for el in working["elements"]]
        return [s for s in valid if s.startswith(text)]
    
    def do_set(self, line):
        '''Set property value for specified object and prop
        
        Usage: set [obj] [propName] [value]
        
        obj: str
            Name of object to modify
        propName: str
            Name of property to modify
        value: Any
            New property value'''

        global working
        if not working: 
            print("Must have open composition!")
            return

        args = parse(line)
        # Input validation
        if type(args[0]) is not str:
            print("Object name must be string!")
            return
        if type(args[1]) is not str:
            print("Property name must be string!")
            return
        
        # Find objects
        obj = None
        for el in working["elements"]:
            if el.name.value == args[0]:
                obj = el
                break
        if obj is None: 
            print("Object not found")
            return
        # Find property
        # prop = None
        for p, v in vars(el).items():
            if p == args[1]:
                # Check types of provided values
                argList = []
                for i in range(len(v.type_)):
                    t = Elements.Property.typemap_str[v.type_[i]]
                    try:
                        arg = t(args[2+i])
                        # Add'l typecheck
                        if not isinstance(arg, t):
                            raise ValueError
                    except ValueError:
                        print(f"Wrong type (param {i}) - type of {p} must be "
                        f"{ [Elements.Property.typemap_str[t] for t in v.type_] }")
                        return
                    except IndexError: 
                        print(f"Not enough arguments: param {p} requires "
                        f"{ [Elements.Property.typemap_str[t] for t in v.type_] }")
                        return
                    # Add arg to list
                    argList.append(arg)

                # Set property value
                if len(argList) > 1:
                    val = tuple(argList)
                else:
                    val = argList[0]
                vars(el)[p]["value"] = val
                print(f"Set {el.name.value}.{p} to {val}")
                # Update JSON, canvas
                write_json()
                refresh_canvas()
                return
                
        # If prop not found
        print("Property not found")
        print("Use `ls` to view object properties")
        return
    
    def complete_set(self, text, line, begidx, endidx):
        numArgs = len(line.split()) + line.endswith(" ")

        valid = []
        if numArgs == 2:
            valid = [el.name.value for el in working["elements"]]
        elif numArgs == 3:
            # Names of properties for selected element
            for el in working["elements"]:
                if el.name.value == line.split()[1]:
                    valid = list(vars(el).keys())
                    break
        return [s for s in valid if s.startswith(text)]

    def do_cp(self, line):
        '''Copy existing element or composition, maintaining all properties
        
        Usage: cp [obj] [newName]
        
        obj: str
            Name of object to copy
        newName: str
            Name of object produced by copy operation'''

        global working

        args = parse(line)
        if len(args) < 2:
            self.do_help("cp")
            return

        if not working: 
            # Check provided value for copyName
            if not re.match("^[A-Za-z0-9_]*$", args[1]):
                print("Invalid composition name.")
                print("Comp names must only contain alphanumeric characters and underscores.")
                return
            
            # If comp file is found, copy file under new name
            srcPath = os.path.join(SRC_PATH, args[0]+".json")
            destPath = os.path.join(SRC_PATH, args[1]+".json")
            # Check for existing comp file
            if not os.path.isfile(srcPath):
                print("Composition file not found")
                return
            fcopy(srcPath, destPath)
            if os.path.isfile(destPath):
                print(f"Copied {args[0]} to {args[1]}.")
            else:
                print("Failed to copy.")
            return
        else: 
            # Check provided copyName for uniqueness
            if args[1] in [el.name for el in working["elements"]]:
                print("Name must be unique (all other args valid).")
                return
        
            for el in working["elements"]:
                if el.name.value == args[0]:
                    elCopy = deepcopy(el)
                    vars(elCopy)["name"]["value"] = args[1]
                    working["elements"].append(elCopy)
                    write_json()
                    # refresh_canvas()
                    return
            print("Object not found.\n")
            self.do_help("cp")
            return

    def complete_cp(self, text, line, begidx, endidx):
        global working
        # Complete comp names if comp is open; else complete element names
        if not working:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []
            
            valid = [os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)]
            return [v for v in valid if v.startswith(text)]
        else:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []

            valid = [el.name.value for el in working["elements"]]
            return [s for s in valid if s.startswith(text)]

    def do_rm(self, line):
        '''Remove existing element or comp
        
        Usage: rm [obj]
        
        obj: str
            Name of object to remove'''

        global working

        args = parse(line)
        if not args: 
            self.do_help("rm")
            return

        if not working: 
            # If no open comp, remove composition file
            srcPath = os.path.join(SRC_PATH, args[0]+".json")
            # Check for existing comp file
            if not os.path.isfile(srcPath):
                print("Composition file not found")
                return
            # Confirm deletion
            while True:
                confirm = input(f"Remove comp {args[0]}? (y/n)")
                confirm = confirm.partition(" ")[0].lower()
                if confirm in ["y", "yes"]: 
                    os.remove(srcPath)
                    if not os.path.exists(srcPath):
                        print(f"Removed {args[0]}.")
                    else:
                        print("Failed to remove.")
                    return
                elif confirm in ["n", "no"]:
                    return 
        else: 
            for el in working["elements"]:
                if el.name.value == args[0]:
                    while True:
                        confirm = input(f"Remove element {args[0]}? (y/n)")
                        confirm = confirm.partition(" ")[0].lower()
                        if confirm in ["y", "yes"]: 
                            working["elements"].remove(el)
                            if el not in working["elements"]:
                                print(f"Removed {args[0]}.")
                            else:
                                print("Failed to remove.")
                            write_json()
                            refresh_canvas()
                            return
                        elif confirm in ["n", "no"]:
                            return 
            print("Object not found.\n")
            self.do_help("rm")
            return

    def complete_rm(self, text, line, begidx, endidx):
        global working
        # Complete comp names if comp is open; else complete element names
        if not working:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []
            
            valid = [os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)]
            return [v for v in valid if v.startswith(text)]
        else:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []

            valid = [el.name.value for el in working["elements"]]
            return [s for s in valid if s.startswith(text)]
        
    def do_close(self, line):
        'Close current working composition'
        global working, canvas, matrix
        if not working:
            # Directly return if no composition is open
            return
        write_json()
        working = {}
        # Reset canvas
        canvas = matrix.CreateFrameCanvas()
        matrix.SwapOnVSync(canvas)

    def do_exit(self, line):
        'Exit ModuleEditor CLI'
        global canvas, matrix
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
    # Generate JSON from element list
    if not working: 
        warn("No open composition, no JSON written", RuntimeWarning)
        return
    workingJson = {}
    for el in working["elements"]:
        elType = ELEMENT_CLASS_NAMES[type(el)]
        if workingJson.get(elType) is None:
            workingJson[elType] = []
        workingJson[elType].append(vars(el))

    with open(working["path"], "w") as file:
        json.dump(workingJson, file, cls=Elements.CEnc)

def print_props(obj: Any):
    '''Print all object properties and their values in formatted output
    
    obj: Any
        Object to print'''
    
    for k, v in vars(obj).items():
        if isinstance(v, Elements.Property):
            print(f"{k}: {v.value}")
        else: 
            print(f"{k}: {v}")

def refresh_canvas():
    global working, canvas, matrix
    if not working:
        raise RuntimeError("Cannot draw without open composition")

    canvas = matrix.CreateFrameCanvas()
    for el in working["elements"]:
        el.draw(canvas)
    matrix.SwapOnVSync(canvas)
    return

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

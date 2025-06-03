# RGB Matrix dependencies
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import config 
from config import FONTS_PATH

# CLI dependencies
import cmd
from modules.src import Elements
from ElementEditor import ElementEditor
import cli
from cli import parse, print_props

import os, re, json
import logging
import traceback
from typing import Any
from warnings import warn
from shutil import copy as fcopy
from copy import deepcopy

# Logger
# N.B. logger used only for system logs. CLI messages made using `print`
import logging
log = logging.getLogger(__name__)

# Standard path to store JSON files at
SRC_PATH = "./display-master/modules/editor/srcFiles"

class ModuleEditor(cmd.Cmd):
    intro = "Welcome to Jaybird's rgbmatrix Module Editor. Type help or ? to list commands.\n"
    prompt = "(ModuleEditor): "

    def __init__(self, matrix, canvas):
        super().__init__()
        self.matrix = matrix
        self.canvas = canvas
        self.working = {}

    #region commands
    def do_new(self, line):
        '''Create new matrix composition

        Usage: new [compName]

        compName: str
            Name of composition (for JSON storage)
        '''

        parentDir = SRC_PATH
        if not os.path.isdir(parentDir): 
            os.mkdir(parentDir)

        # Parse & check number of arguments
        args = parse(line)
        if not args: 
            # Print docs if no arguments given
            self.do_help("new")
            return
        
        (compName,) = args
        if not re.match("^[A-Za-z0-9_]*$", compName):
            print("Invalid name.")
            print("Comp names must only contain alphanumeric characters and underscores.")
            return

        self.working = {}
        path_ = os.path.join(parentDir,compName + ".json")
        if os.path.exists(path_): 
            while True:
                confirm = input("This path already exists!  Do you want to over[w]rite, "
                                "[o]pen, or [c]ancel? (w/o/c)")
                confirm = confirm.partition(" ")[0].lower()
                if confirm in ["w", "overwrite", "write"]: 
                    break
                elif confirm in ["o", "open"]: 
                    self.do_open(compName)
                    break
                elif confirm in ["c", "cancel"]: 
                    self.working = {}
                    print("Canceled creating composition.")
                    return
                else: 
                    print("Invalid response.")
        # Set comp properties
        self.working["name"] = compName
        self.working["path"] = path_
        self.working["elements"] = []
        log.debug(self.working)

    def do_open(self, line):
        '''Open matrix composition JSON file

        Usage: open [comp]

        comp: str
            Name of JSON file to open
        '''

        args = parse(line)
        if not args: 
            # Print docs if no arguments given
            self.do_help("open")
            return

        if self.working: 
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
        log.debug(path)
        if not os.path.isfile(path):
            print("First argument must be valid composition name")
            print("Use `ls` to see existing comps or `new` to create a comp")
            return
        
        # path = os.path.join(SRC_PATH, "tempName.json")
        log.debug(path)
        with open(path) as file:
            self.working["name"] = args[0]
            self.working["path"] = path
            jsonFile = json.load(file)
            #Populate element list -- iterate over classes, then objects
            self.working["elements"] = []
            for k, v in jsonFile.items():
                for props in v:
                    newEl = cli.ELEMENT_TYPES[k].from_dict(props)
                    # log.debug(newEl.__dict__)
                    self.working["elements"].append(newEl)
            self.refresh_canvas()

    def complete_open(self, text, line, begidx, endidx):
        log.debug(f"args: {text}, {line}, {begidx}, {endidx}")
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

        # Check for open composition
        if not self.working: 
            print("Must have open composition! \nUse `new` to create a comp or `open` to import one from JSON.")
            return
        
        log.debug(line)
        args = parse(line)
        # Input validation
        if len(args) < 1 or args[0] not in cli.ELEMENT_TYPES.keys():
            # Validate element type
            print("Select an element type to add:\n" + str(list(cli.ELEMENT_TYPES.keys())))
            return

        elType = args[0]
        # Take element type, then prompt for other arguments
        elArgs = []
        for pi in range(len(cli.ELEMENT_TYPES[elType].params)):
            # Prompt for next parameter
            curParam = cli.ELEMENT_TYPES[elType].params[pi]
            elArgs.append(input(f"{curParam.name} ({str(curParam.type)}): "))

        # elArgs = args[1:]
        # invalidArgs = cli.ELEMENT_TYPES[elType].testArgs(*elArgs)
        # if invalidArgs:
        #     print(invalidArgs)
        #     print(cli.ELEMENT_TYPES[elType].docstr)
        #     return
        # if elArgs[0] in [el.name for el in self.working["elements"]]:
        #     print("Name must be unique (all other args valid).")
        #     return
        try: 
            # Test arguments
            argErrs = cli.ELEMENT_TYPES[elType].testArgs(*elArgs)
            if argErrs is None: 
                newEl = cli.ELEMENT_TYPES[elType](*elArgs)
            else:
                log.error(argErrs)
                return
        except Exception as e: 
            # Handle exceptions non-fatally
            log.error(e)
            log.debug(f"Traceback: {traceback.extract_tb(e.__traceback__)}")
            return
        

        self.working["elements"].append(newEl)
        self.update_all()

    def complete_add(self, text, line, begidx, endidx):
        # Ignore completion after first argument
        if len(line.split()) + line.endswith(" ") > 2: 
            return []

        valid = list(cli.ELEMENT_TYPES.keys())
        return [s for s in valid if s.startswith(text)]

    def do_ls(self, line):
        '''Print list of elements in current directory
        
        Usage: ls [?obj]
        
        obj: str (optional)
            Name of object to print
            Prints object properties'''
        
        args = parse(line)

        if not args: 
            if not self.working: 
                # If no open comp, print composition files
                print(*[os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)], sep="\t\t")
            else: 
                print(*[el.name.value for el in self.working["elements"]], sep="\t\t")
            return
        else: 
            for el in self.working["elements"]:
                if el.name.value == args[0]:
                    print_props(el)
                    return
        print("Object not found.\n")
        self.do_help("ls")
        return

    def complete_ls(self, text, line, begidx, endidx):
        # Ignore after 1st argument
        if not self.working or (len(line.split()) + line.endswith(" ") > 2):
            return []

        valid = [el.name.value for el in self.working["elements"]]
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

        if not self.working: 
            print("Must have open composition!")
            return

        args = parse(line)
        # Input validation
        minargs = 3
        if len(args) < minargs: 
            print("Not enough arguments.")
            self.do_help("set")
            return
        if type(args[0]) is not str:
            print("Object name must be string!")
            return
        if type(args[1]) is not str:
            print("Property name must be string!")
            return
        
        # Find objects
        obj = None
        for el in self.working["elements"]:
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
                elArgs = []
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
                    elArgs.append(arg)

                # Get requested value from cmd args
                if len(elArgs) > 1:
                    val = tuple(elArgs)
                else:
                    val = elArgs[0]

                # Test for value in list of accepted values
                if v.mode == "s" and val not in v.options:
                    print(f"Value {val} not in allowed values")
                    print(f"Choose one of: {v.options}")
                    return
                
                # Set property value
                vars(el)[p]["value"] = val
                print(f"Set {el.name.value}.{p} to {val}")
                self.update_all()
                return
                
        # If prop not found
        print("Property not found")
        print("Use `ls` to view object properties")
        return
    
    def complete_set(self, text, line, begidx, endidx):
        numArgs = len(line.split()) + line.endswith(" ")

        valid = []
        if numArgs == 2:
            valid = [el.name.value for el in self.working["elements"]]
        elif numArgs == 3:
            # Names of properties for selected element
            for el in self.working["elements"]:
                if el.name.value == line.split()[1]:
                    valid = list(vars(el).keys())
                    break
        return [s for s in valid if s.startswith(text)]

    def do_edit(self, line):
        '''Select object for extended editing
        
        Usage: edit [obj]
        
        obj: str
            Name of object to modify'''

        if not self.working: 
            print("Must have open composition!")
            return

        # Parse & check arguments
        args = parse(line)
        if not args: 
            self.do_help("edit")
            return
        
        # Find objects
        obj = None
        for el in self.working["elements"]:
            if el.name.value == args[0]:
                obj = el
                break
        if obj is None: 
            print("Object not found")
            return

        # Start object editor CLI
        ElementEditor(obj, self).cmdloop()

    def complete_edit(self, text, line, begidx, endidx):
        numArgs = len(line.split()) + line.endswith(" ")

        valid = []
        if numArgs == 2:
            valid = [el.name.value for el in self.working["elements"]]
        return [s for s in valid if s.startswith(text)]

    def do_cp(self, line):
        '''Copy existing element or composition, maintaining all properties
        
        Usage: cp [obj] [newName]
        
        obj: str
            Name of object to copy
            May be Element or composition
        newName: str
            Name of object produced by copy operation
            Convention must match that of `obj`'''

        # Parse & check arguments
        args = parse(line)
        minargs = 2
        if len(args) < minargs:
            print("Not enough arguments.")
            self.do_help("cp")
            return

        if not self.working: 
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
            if args[1] in [el.name for el in self.working["elements"]]:
                print("Name must be unique (all other args valid).")
                return
        
            for el in self.working["elements"]:
                if el.name.value == args[0]:
                    elCopy = deepcopy(el)
                    vars(elCopy)["name"]["value"] = args[1]
                    self.working["elements"].append(elCopy)
                    self.update_all()
                    return
            print("Object not found.\n")
            self.do_help("cp")
            return

    def complete_cp(self, text, line, begidx, endidx):
        # Complete comp names if comp is open; else complete element names
        if not self.working:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []
            
            valid = [os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)]
            return [v for v in valid if v.startswith(text)]
        else:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []

            valid = [el.name.value for el in self.working["elements"]]
            return [s for s in valid if s.startswith(text)]

    def do_rm(self, line):
        '''Remove existing element or comp
        
        Usage: rm [obj]
        
        obj: str
            Name of object to remove'''

        args = parse(line)
        if not args: 
            self.do_help("rm")
            return

        if not self.working: 
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
            for el in self.working["elements"]:
                if el.name.value == args[0]:
                    while True:
                        confirm = input(f"Remove element {args[0]}? (y/n)")
                        confirm = confirm.partition(" ")[0].lower()
                        if confirm in ["y", "yes"]: 
                            self.working["elements"].remove(el)
                            if el not in self.working["elements"]:
                                print(f"Removed {args[0]}.")
                            else:
                                print("Failed to remove.")
                            self.update_all()
                            return
                        elif confirm in ["n", "no"]:
                            return 
            print("Object not found.\n")
            self.do_help("rm")
            return

    def complete_rm(self, text, line, begidx, endidx):
        # Complete comp names if comp is open; else complete element names
        if not self.working:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []
            
            valid = [os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)]
            return [v for v in valid if v.startswith(text)]
        else:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []

            valid = [el.name.value for el in self.working["elements"]]
            return [s for s in valid if s.startswith(text)]
        
    def do_close(self, line):
        '''Closes current working composition
        
        Usage: close'''
        if not self.working:
            # Directly return if no composition is open
            return
        self.write_json()
        self.working = {}
        # Reset canvas
        self.canvas = self.matrix.CreateFrameCanvas()
        self.matrix.SwapOnVSync(self.canvas)

    def do_export(self, line):
        '''Exports composition as Python file with same name. Exports current comp
        if any is open; otherwise exports comp with provided name
        
        Usage: export [compName]
        
        compName: name of composition to export'''

        if self.working: 
            # Export current composition if there is one open
            cli.export_code(self.working["name"], self.working["elements"])
        else: 
            # Export comp name provided in argument
            # (compName,) = cli.parse(line)
            # Parse & check args
            args = parse(line)
            if not args: 
                self.do_help("export")
                return
            (compName,) = args

            # Check compName validity
            path = os.path.join(SRC_PATH, compName + ".json")
            # LOG: path being checked
            if not os.path.isfile(path):
                print("First argument must be valid composition name")
                print("Use `ls` to see existing comps or `new` to create a comp")
                return
            # Export comp
            self.do_open(compName)
            cli.export_code(self.working["name"], self.working["elements"])
            self.do_close(None)

    def complete_export(self, text, line, begidx, endidx):
        # Ignore after 1st argument, or if open comp
        if self.working or len(line.split()) + line.endswith(" ") > 2: 
            return []
        valid = [os.path.splitext(p)[0] for p in os.listdir(SRC_PATH)]
        return [v for v in valid if v.startswith(text)]    

    def do_exit(self, line):
        '''Exits ModuleEditor CLI and closes open composition (if any)
        
        Usage: exit'''
        print("Closing ModuleEditor...")
        self.do_close(None)
        self.canvas.Clear()
        self.matrix.SwapOnVSync(self.canvas)
        return True 

    #endregion


    #region Helper Methods

    def new_json(self):
        '''Generates fresh JSON template

        Creates sub-dict for each class name in ELEMENT_TYPES
        '''
        outDict = {}
        for t in cli.ELEMENT_TYPES:
            outDict[t] = {}
        return outDict

    def write_json(self):
        'Write changes to JSON file'
        # Generate JSON from element list
        if not self.working: 
            warn("No open composition, no JSON written", RuntimeWarning)
            return
        workingJson = {}
        for el in self.working["elements"]:
            elType = cli.ELEMENT_CLASS_NAMES[type(el)]
            if workingJson.get(elType) is None:
                workingJson[elType] = []
            workingJson[elType].append(vars(el))

        with open(self.working["path"], "w") as file:
            json.dump(workingJson, file, cls=Elements.CEnc)

    def refresh_canvas(self):
        if not self.working:
            raise RuntimeError("Cannot draw without open composition")

        # canvas = self.matrix.CreateFrameCanvas()
        self.canvas.Clear()
        for el in self.working["elements"]:
            el.draw(self.canvas)
        self.matrix.SwapOnVSync(self.canvas)
        return

    def sort_working(self):
        '''Sort working dictionary by layer, then re-index element layers based on new positions'''
        self.working["elements"].sort(key=lambda el: el.layer.value)
        for i in range(len(self.working["elements"])):
            el = self.working["elements"][i]
            el.layer.value = i

    def update_all(self, do_sort: bool = True, do_reindex: bool = True, do_write_json: bool = True, do_refresh_canvas: bool = True):
        '''Sort working dictionary by layer, then update JSON file and matrix display
        
        do_sort: runs sort_working() if true
        do_write_json: runs write_json() if true
        do_refresh_canvas: runs refresh_canvas() if true'''

        # if do_sort: sort_working()
        if "elements" in self.working:
            if do_sort: self.working["elements"].sort(key=lambda el: el.layer.value)
            if do_reindex: 
                for i in range(len(self.working["elements"])):
                    el = self.working["elements"][i]
                    el.layer.value = i
        if do_refresh_canvas: self.refresh_canvas()
        if do_write_json: self.write_json()

    def export_code(self, fileName: str, compElements: list):
        '''Exports current composition as Python code and writes to output file.
        N.B. all code used for exporting must use 4-space tabs (not 2-space or tab chars).
        
        fileName: name of new file to be created (no extension)
            Must only be composed of alphanumeric chars and underscores
            (Same convention as composition names)
        compElements: list of elements in composition to be exported 
            (will usually be working["elements"])'''

        exportPath = f"../exports/{fileName}.py"

        fcopy("./matrixBoilerplate.py", exportPath)
        # Copy boilerplate file and append element code
        with open(exportPath, 'a') as codeFile: 
            for el in compElements: 
                codeFile.write(el.draw_code() + "\n")
            # Append final code
            codeFile.write("    canvas = matrix.SwapOnVSync(canvas)\n\n"
                        "if __name__ == '__main__':\n"
                        "    main()")
            
        # Update file permissions -- add write permission to group
        os.chmod(exportPath, 0o664)
        print(f"Exported comp {fileName} as {fileName}.py")
    
    #endregion
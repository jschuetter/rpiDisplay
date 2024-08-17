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
from ElementEditor import ElementEditor
import cli # Relevant global vars & methods
from cli import working, parse, \
    refresh_canvas, write_json, print_props, update_all

import os, re, json
import logging
from typing import Any
from warnings import warn
from shutil import copy as fcopy
from copy import deepcopy

class ModuleEditor(cmd.Cmd):
    intro = "Welcome to Jaybird's rgbmatrix Module Editor. Type help or ? to list commands.\n"
    prompt = "(ModuleEditor): "

    def do_new(self, line):
        '''Create new matrix composition

        Usage: new [compName]

        compName: str
            Name of composition (for JSON storage)
        '''

        global working

        parentDir = cli.SRC_PATH
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

        global working

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

        path = os.path.join(cli.SRC_PATH, args[0] + ".json")
        print(path)
        if not os.path.isfile(path):
            print("First argument must be valid composition name")
            print("Use `ls` to see existing comps or `new` to create a comp")
            return
        
        # path = os.path.join(SRC_PATH, "tempName.json")
        print(path)
        with open(path) as file:
            working["name"] = args[0]
            working["path"] = path
            jsonFile = json.load(file)
            #Populate element list -- iterate over classes, then objects
            working["elements"] = []
            for k, v in jsonFile.items():
                for props in v:
                    newEl = cli.ELEMENT_TYPES[k].from_dict(props)
                    # print(newEl.__dict__)
                    working["elements"].append(newEl)
            refresh_canvas()

    def complete_open(self, text, line, begidx, endidx):
        # print(f"args: {text}, {line}, {begidx}, {endidx}")
        # Ignore after 1st argument
        if len(line.split()) + line.endswith(" ") > 2: 
            return []
        
        valid = [os.path.splitext(p)[0] for p in os.listdir(cli.SRC_PATH)]
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

        global working
        # Check for open composition
        if not working: 
            print("Must have open composition! \nUse `new` to create a comp or `open` to import one from JSON.")
            return
        
        cli.log.debug(line)
        args = parse(line)
        # Input validation
        if len(args) < 1 or args[0] not in cli.ELEMENT_TYPES.keys():
            # Validate element type
            print("Select an element type to add:\n" + str(list(cli.ELEMENT_TYPES.keys())))
            return

        elType = args[0]
        elArgs = args[1:]
        invalidArgs = cli.ELEMENT_TYPES[elType].testArgs(*elArgs)
        if invalidArgs:
            print(invalidArgs)
            print(cli.ELEMENT_TYPES[elType].docstr)
            return
        if elArgs[0] in [el.name for el in working["elements"]]:
            print("Name must be unique (all other args valid).")
            return
        newEl = cli.ELEMENT_TYPES[elType](*elArgs)

        working["elements"].append(newEl)
        update_all()

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
        
        global working

        args = parse(line)

        if not args: 
            if not working: 
                # If no open comp, print composition files
                print(*[os.path.splitext(p)[0] for p in os.listdir(cli.SRC_PATH)], sep="\t\t")
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

                # Test for value in list of accepted values
                if v.mode == "s" and val not in v.options:
                    print(f"Value {val} not in allowed values")
                    print(f"Choose one of: {v.options}")
                    return
                
                # Set property value
                if len(argList) > 1:
                    val = tuple(argList)
                else:
                    val = argList[0]
                vars(el)[p]["value"] = val
                print(f"Set {el.name.value}.{p} to {val}")
                update_all()
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

    def do_edit(self, line):
        '''Select object for extended editing
        
        Usage: edit [obj]
        
        obj: str
            Name of object to modify'''

        global working
        if not working: 
            print("Must have open composition!")
            return

        args = parse(line)
        
        # Find objects
        obj = None
        for el in working["elements"]:
            if el.name.value == args[0]:
                obj = el
                break
        if obj is None: 
            print("Object not found")
            return

        # Start object editor CLI
        ElementEditor(obj).cmdloop()

    def complete_edit(self, text, line, begidx, endidx):
        numArgs = len(line.split()) + line.endswith(" ")

        valid = []
        if numArgs == 2:
            valid = [el.name.value for el in working["elements"]]
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
            srcPath = os.path.join(cli.SRC_PATH, args[0]+".json")
            destPath = os.path.join(cli.SRC_PATH, args[1]+".json")
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
                    update_all()
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
            
            valid = [os.path.splitext(p)[0] for p in os.listdir(cli.SRC_PATH)]
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
            srcPath = os.path.join(cli.SRC_PATH, args[0]+".json")
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
                            update_all()
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
            
            valid = [os.path.splitext(p)[0] for p in os.listdir(cli.SRC_PATH)]
            return [v for v in valid if v.startswith(text)]
        else:
            # Ignore after first argument
            if len(line.split()) + line.endswith(" ") > 2: 
                return []

            valid = [el.name.value for el in working["elements"]]
            return [s for s in valid if s.startswith(text)]
        
    def do_close(self, line):
        '''Closes current working composition
        
        Usage: close'''
        global working
        if not working:
            # Directly return if no composition is open
            return
        write_json()
        working = {}
        # Reset canvas
        cli.canvas = cli.matrix.CreateFrameCanvas()
        cli.matrix.SwapOnVSync(cli.canvas)

    def do_export(self, line):
        '''Exports composition as Python file with same name. Exports current comp
        if any is open; otherwise exports comp with provided name
        
        Usage: export [compName]
        
        compName: name of composition to export'''

        global working
        if working: 
            # Export current composition if there is one open
            cli.export_code(working["name"], working["elements"])
        else: 
            # Export comp name provided in argument
            (compName,) = cli.parse(line)
            # Check compName validity
            path = os.path.join(cli.SRC_PATH, compName + ".json")
            # LOG: path being checked
            if not os.path.isfile(path):
                print("First argument must be valid composition name")
                print("Use `ls` to see existing comps or `new` to create a comp")
                return
            # Export comp
            self.do_open(compName)
            cli.export_code(working["name"], working["elements"])
            self.do_close(None)

    def complete_export(self, text, line, begidx, endidx):
        # Ignore after 1st argument, or if open comp
        global working
        if working or len(line.split()) + line.endswith(" ") > 2: 
            return []
        valid = [os.path.splitext(p)[0] for p in os.listdir(cli.SRC_PATH)]
        return [v for v in valid if v.startswith(text)]    

    def do_exit(self, line):
        '''Exits ModuleEditor CLI and closes open composition (if any)
        
        Usage: exit'''
        print("Closing ModuleEditor...")
        self.do_close(None)
        cli.canvas.Clear()
        cli.matrix.SwapOnVSync(cli.canvas)
        return True


if __name__ == "__main__":
   ModuleEditor().cmdloop() 
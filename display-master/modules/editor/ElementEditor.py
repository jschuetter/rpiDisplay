import cmd
from modules.src import Elements
from modules.src.Elements import Property
import cli
from cli import parse
import sys, tty, termios
from copy import deepcopy

# Logger
# N.B. logger used only for system logs. CLI messages made using `print`
import logging
log = logging.getLogger(__name__)

class ElementEditor(cmd.Cmd):
    def __init__(self, obj_, meditor_):
        super().__init__()
        self.obj = obj_
        self.meditor = meditor_
        self.intro = f"Editing {obj_}:"
        self.prompt = f"{obj_.name.value}> "

    def do_set(self, line):
        '''Set property value for specified object and prop
        
        Usage: set [propName] [?value]
        
        propName: str
            Name of property to modify
        value: Any (optional)
            New property value'''

        args = parse(line)
        propName = None
        prop = None
        value = None
        if len(args) < 1: 
            self.do_help("set")
            return
        if len(args) >= 2:
            value = args[1:]

        # Find property
        for p, v in vars(self.obj).items():
            if p == args[0]:
                propName = p
                prop = v
                break
        
        if prop is None:
            # If prop not found
            print("Property not found")
            print("Use `ls` to view object properties")
            return

        if value is None:
            # If prop is found and no value is provided, prompt for value
            # Start new input window
            print(f"Editing property {propName}")
            self.capture_input(prop, propName)
                
        else: 
            # Handle arguments provided on command line
            # Check types of provided values
            argList = []
            for i in range(len(prop.type_)):
                t = Elements.Property.typemap_str[prop.type_[i]]
                try:
                    arg = t(args[1+i])
                    # Add'l typecheck
                    if not isinstance(arg, t):
                        raise ValueError
                except ValueError:
                    print(f"Wrong type (param {i}) - type of {p} must be "
                    f"{ [Elements.Property.typemap_str[t] for t in prop.type_] }")
                    return
                except IndexError: 
                    print(f"Not enough arguments: param {p} requires "
                    f"{ [Elements.Property.typemap_str[t] for t in prop.type_] }")
                    return
                # Add arg to list
                argList.append(arg)

            # Set property value
            if len(argList) > 1:
                val = list(argList)
            else:
                val = argList[0]

            # Test for value in list of accepted values
            if prop.mode == "s" and val not in prop.options:
                print(f"Value {val} not in allowed values")
                print(f"Choose one of: {prop.options}")
                return
            
            vars(self.obj)[p]["value"] = val
            print(f"Set {self.obj.name.value}.{propName} to {val}")
            # Update JSON, canvas
            self.meditor.update_all()
            return
    
    def complete_set(self, text, line, begidx, endidx):
        numArgs = len(line.split()) + line.endswith(" ")

        valid = []
        if numArgs == 2:
            valid = list(vars(self.obj).keys())
        return [s for s in valid if s.startswith(text)]

    def capture_input(self, prop, propName):
        print(f"{propName}: {prop.type_}, {Property.modemap[prop.mode]}")
        print(f"- {Property.modehints[prop.mode]}\n")

        # Save the current terminal settings

        def getch():
            fd = sys.stdin.fileno()
            oldSettings = termios.tcgetattr(fd)
            try:
                # Set terminal to raw mode
                tty.setraw(sys.stdin.fileno())
                # Loop
                while True:
                    # Read a single character
                    ch = sys.stdin.read(1)
                    
                    if ch in ['\x0a', '\x0d', '\x03', '\x04']:
                        # Break on return char or EOF/EOT
                        yield ch
                        return
                    elif ch == '\x1b':
                        # Read escape char, then look for arrow key values
                        ch = sys.stdin.read(1)
                        if ch == '[':
                            ch = sys.stdin.read(1)
                            if ch == 'A':
                                yield "up"
                            elif ch == 'B':
                                yield "down"
                            elif ch == 'C':
                                yield "right"
                            elif ch == 'D':
                                yield "left"
                            else:
                                print("Unknown sequence")
                        else: 
                            print("Unknown sequence")
                    else: 
                        yield ch
            finally:
                # Restore the original terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

        def _check_type(valList):
            argList = []
            for i in range(len(prop.type_)):
                t = Elements.Property.typemap_str[prop.type_[i]]
                try:
                    arg = t(valList[i])
                    # Add'l typecheck
                    if not isinstance(arg, t):
                        raise ValueError
                except ValueError:
                    print(f"Wrong type (param {i}) - type of {propName} must be "
                    f"{ [Elements.Property.typemap_str[t] for t in prop.type_] }")
                    return
                except IndexError: 
                    print(f"Not enough arguments: param {propName} requires "
                    f"{ [Elements.Property.typemap_str[t] for t in prop.type_] }")
                    return
                # Add arg to list
                argList.append(arg)
            return argList
    
        if prop.mode == "s":
            # If property is scrollable, allow entering literal value 
            # or scrolling through values
            scrollInd = 0
            origValue = deepcopy(prop.value)
            for char in getch():
                sys.stdout.write('\x1b[2K') # Clear line
                if char in ('up', 'w'):
                    scrollInd += 1
                    if scrollInd >= len(prop.options): 
                        scrollInd = 0
                    print(prop.options[scrollInd], end="\r")
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = prop.options[scrollInd]
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char in ('down', 's'):
                    scrollInd -= 1
                    if scrollInd <= -1:
                        scrollInd = len(prop.options) - 1
                    print(prop.options[scrollInd], end="\r")
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = prop.options[scrollInd]
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char == '\x03':
                    # If Ctrl+C received, cancel input
                    print("Cancelling input", end = '\r\n')
                    vars(self.obj)[propName]["value"] = origValue
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                    return
                
            # On return, set property value
            # Encapsulate value in list to allow proper typechecking 
            valArgs = [prop.options[scrollInd],]
            # Value typechecking
            argList = _check_type(valArgs)

            # Set property value
            if len(argList) > 1:
                val = list(argList)
            else:
                val = argList[0]
            vars(self.obj)[propName]["value"] = val
            log.debug(f"Set {propName} to {val}")
            print(f"Set {self.obj.name.value}.{propName} to {val}")
            self.meditor.update_all()
            return
                
        elif prop.mode == "n":
            # If property is numeric, allow entering literal value 
            # or nudging value
            origValue = deepcopy(prop.value)
            for char in getch():
                val = prop.value
                # Clear line for input
                sys.stdout.write('\x1b[2K')
                if char in ('up', 'w'):
                    val += 1
                    print(val, end='\r')
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = val
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char in ('down', 's'):
                    val -= 1
                    print(val, end='\r')
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = val
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char == '\x03':
                    # If Ctrl+C received, cancel input
                    print("Cancelling input", end='\r\n')
                    vars(self.obj)[propName]["value"] = origValue
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                    return
                
            # On return, set property value
            # Value typechecking
            argList = _check_type([val])

            # Set property value
            if len(argList) > 1:
                val = list(argList)
            else:
                val = argList[0]
            vars(self.obj)[propName]["value"] = val
            print(f"Set {self.obj.name.value}.{propName} to {val}")
            self.meditor.update_all()
            return
            
        elif prop.mode == "n2":
            # If property is numeric, allow entering literal value 
            # or nudging value
            origValue = deepcopy(prop.value)
            val = prop.value
            for char in getch():
                if char in ('right', 'd'):
                    val[0] += 1
                    print(val, end='\r')
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = val
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char in ('left', 'a'):
                    val[0] -= 1
                    print(val, end='\r')
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = val
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char in ('up', 'w'):
                    val[1] += 1
                    print(val, end='\r')
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = val
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char in ('down', 's'):
                    val[1] -= 1
                    print(val, end='\r')
                    # Update values, canvas
                    vars(self.obj)[propName]["value"] = val
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                elif char == '\x03':
                    # If Ctrl+C received, cancel input
                    print("Cancelling input", end='\r\n')
                    vars(self.obj)[propName]["value"] = origValue
                    self.meditor.update_all(do_reindex=False, do_write_json=False)
                    return
                
            # On return, set property value
            # Value typechecking
            argList = _check_type(val)

            # Set property value
            if len(argList) > 1:
                val = list(argList)
            else:
                val = argList[0]
            vars(self.obj)[propName]["value"] = val
            print(f"Set {self.obj.name.value}.{propName} to {val}")
            self.meditor.update_all()
            return
        
        elif prop.mode == "l":
            # If literal value only, take value as command-line argument
            self.do_help("set")
            return
        
        else: 
            # Invalid mode, should not occur
            raise ValueError(f"Invalid property mode: {propName}:{prop.mode}")


    def do_ls(self, line):
        '''Print list of properties of current element
        
        Usage: ls'''

        for (prop, data) in vars(self.obj).items(): 
            try: 
                print(f"\t{prop}: {data.value}")
            except AttributeError as ae: 
                print(f"\t{prop}: {data}")
                # log.warning(ae)
        return

    def do_done(self, line):
        '''Exit ModuleEditor CLI
        
        Usage: done'''
        print("Returning to ModuleEditor...")
        return True
#!/bin/python
'''
Raspberry Pi RGB Matrix Display Project
Version 0.1.0
Jacob Schuetter

Project history: 
- First commit: 19 Jun 2024
- Last commit: 16 Feb 2025
v0.0.1: main.py created, handles running modules behind CLI "controller"; modules updated to class scheme
v0.0.2: logging module implemented, to both alternate terminal ouptut and file output
v0.1.0: first working version of editor module added

This file: 
Current version contains command-line interface for calling existing modules from project root directory
- Created: 09 Feb 2025
- Updated 22 May 2025
'''

from cmd import Cmd
import os, sys, threading

# Add subfolders to sys.path
CODE_PATH = "./display-master"
for root, dirs, files in os.walk(CODE_PATH): 
    sys.path.append(root)
import config

# Logger
import logging
logFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# logging.basicConfig(
#     level=logging.DEBUG,
#     # stream=sys.stdout,
#     # stream=logTerminal,
#     filename=config.LOG_FILE,
#     format=logFormat
# )
log = logging.getLogger()
log.setLevel(logging.DEBUG)
# Set up handlers for log -- log all to file; 
#   output WARN and above to stdout

# File handler (logs everything)
file_handler = logging.FileHandler(config.LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Stream handler for stdout (only WARNING and above)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.WARNING)
stdout_formatter = logging.Formatter('%(levelname)s: %(message)s')
stdout_handler.setFormatter(stdout_formatter)

# Add both handlers to the logger
log.addHandler(file_handler)
log.addHandler(stdout_handler)

# ThreadLoop helper class, to run modules behind main CLI
from ThreadLoop import ThreadLoop

# Import modules
from clocks.basicclock import BasicClock
from editor.base import Editor
from testmodule import TestModule
# from fonttest import Fonttest
MODULES_PATH = "./display-master/modules"
MODULES = {
    "basicclock": BasicClock,
    "editor": Editor,
    "testmodule": TestModule
}

# Other dependencies
import time

# Define matrix from config file
matrix = config.matrix_from_env()

def clearMatrix():
    'Basic helper method for clearing matrix after module stop'
    blank = matrix.CreateFrameCanvas()
    matrix.SwapOnVSync(blank)

modRunning = False # Indicates whether a module is currently running
modThread = None

class MyShell(Cmd):
    # Define the prompt for the shell
    prompt = '> '
    log.info("Begin session")
    
    def do_about(self, arg):
        '''Give project information'''
        print(__doc__)
    
    def do_run(self, arg):
        '''Run module by calling Python script'''
        global modRunning, modThread

        if not arg:
            # Do nothing if no args provided
            return
        if modRunning: 
            print("There is already a module running!")
            return
        
        (modname,) = arg.split()
        try:
            mod = MODULES[modname](matrix)
            log.info(f"Started module {modname}")
            modRunning = True
        except KeyError as e:
            log.error(e)
            return

        mod.draw()

        if mod.doloop:
            modThread = ThreadLoop(mod.delay, mod.loop)

        # while mod.doloop: 
        #     mod.loop()
        #     time.sleep(mod.delay)

    def complete_run(self, text, line, begidx, endidx):
        # Ignore after 1st argument
        if len(line.split()) + line.endswith(" ") > 2: 
            return []
        
        valid = list(MODULES.keys())
        return [v for v in valid if v.startswith(text)]
    
    # Alias do_run
    do_r = do_run
    complete_r = complete_run

    def do_stop(self, arg):
        '''Stops a running module'''
        global modRunning, modThread
        if modRunning:
            if modThread: modThread.stop()
            clearMatrix()
            log.info("Module stopped.")
            modRunning = False
        else: 
            return

    def do_clearlog(self, arg):
        '''Clear logging file output'''
        confirm = input("Are you sure? (y/n) ")
        if confirm in ["y", "yes"]:
            with open(config.LOG_FILE, 'w'):
                # Truncate file contents
                pass
            print(f"Cleared log file {config.LOG_FILE}")
        else: 
            print("Canceled.")
    
    def do_quit(self, arg):
        '''Exit the shell.'''
        print("Closing...")
        # Close secondary logging terminal
        log.info("End session.")
        return True  # Returning True ends the shell

    # Alias do_quit
    do_exit = do_quit

    # Hide aliases from help list
    hidden_aliases = ["do_r", "do_exit"]

    def get_names(self): 
        return [n for n in dir(self.__class__) if n not in self.hidden_aliases]

# Main entry point for running the shell
if __name__ == '__main__':
    shell = MyShell()
    shell.cmdloop()

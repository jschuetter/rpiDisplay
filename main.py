#!/bin/python
'''
Raspberry Pi RGB Matrix Display Project
Version 0.0.2
Jacob Schuetter

Project history: 
- First commit: 19 Jun 2024
- Last commit: 16 Feb 2025
v0.0.1: main.py created, handles running modules behind CLI "controller"; modules updated to class scheme
v0.0.2: logging module implemented, to both alternate terminal ouptut and file output

This file: 
Current version contains command-line interface for calling existing modules from project root directory
- Created: 09 Feb 2025
- Updated 16 Feb 2025
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
logging.basicConfig(
    level=logging.DEBUG,
    # stream=sys.stdout,
    # stream=logTerminal,
    filename=config.LOG_FILE,
    format=logFormat
)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# ThreadLoop helper class, to run modules behind main CLI
from ThreadLoop import ThreadLoop

# Import modules
from clocks.basicclock import BasicClock
from editor.base import Editor
# from comp import Comp
MODULES_PATH = "./display-master/modules"
MODULES = {
    "basicclock": BasicClock,
    "editor": Editor
    # "comp": Comp
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
        except KeyError as e:
            print(e)
            return

        mod.draw()

        if mod.doloop:
            modRunning = True
            modThread = ThreadLoop(mod.delay, mod.loop)

        # while mod.doloop: 
        #     mod.loop()
        #     time.sleep(mod.delay)

    # Alias do_run
    do_r = do_run

    def do_stop(self, arg):
        '''Stops a running module'''
        global modRunning, modThread
        if modRunning:
            modThread.stop()
            clearMatrix()
            print("Module stopped.")
            modRunning = False
        else: 
            return

    def do_clearLog(self, arg):
        '''Clear logging file output'''
        confirm = input("Are you sure? (y/n)")
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

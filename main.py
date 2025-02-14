#!/bin/python
'''
Raspberry Pi RGB Matrix Display Project
Version 0.0.1
Jacob Schuetter

Project history: 
- First commit: 19 Jun 2024
- Last commit: 09 Feb 2025

This file: 
Current version contains command-line interface for calling existing modules from project root directory
- Created: 09 Feb 2025
'''

from cmd import Cmd
import subprocess, runpy, os, sys

# Logger
import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Add subfolders to sys.path
CODE_PATH = "./display-master"
for root, dirs, files in os.walk(CODE_PATH): 
    sys.path.append(root)
import config
log.debug(sys.path)

# Import modules
from basicclock.base import BasicClock
from editor.base import Editor
MODULES_PATH = "./display-master/modules"
MODULES = {
    "basicclock": BasicClock,
}

# Other dependencies
import time

# Define matrix from config file
matrix = config.matrix_from_env()

class MyShell(Cmd):
    # Define the prompt for the shell
    prompt = '> '
    log.debug(os.getcwd())
    
    def do_about(self, arg):
        '''Give project information'''
        print(__doc__)
    
    def do_run(self, arg):
        '''Run module by calling Python script'''
        # bc = BasicClock(matrix)
        # while True: 
        #     bc.loop()
        #     time.sleep(bc.delay)
        ed = Editor(matrix)

    
    def do_quit(self, arg):
        '''Exit the shell.'''
        print("Goodbye!")
        return True  # Returning True ends the shell

    # Define aliases
    def get_names(self):
        '''Define command aliases'''
        return {
            "run": ["r"],
            "quit": ["exit"]
        }
    
    # A command for help in the shell
    # def do_help(self, arg):
    #     """List available commands."""
    #     print("Available commands:")
    #     print("  greet <name>  - Greets the user with the given name.")
    #     print("  add <num1> <num2>  - Adds two numbers and prints the result.")
    #     print("  quit  - Exits the shell.")
    
    # Optional: Override the default method for unknown commands
    # def default(self, line):
    #     print(f"Unknown command: {line}")

# Main entry point for running the shell
if __name__ == '__main__':
    shell = MyShell()
    shell.cmdloop()

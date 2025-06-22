#!/bin/python
'''
progressBar.py
22 June 2025
Jacob Schuetter

Helper method for printing progress bar to terminal
'''
def printProgress(current, total, *, length=25, crOnDone=True):
    print("[", end="")
    for i in range(length):
        if i < (current / total) * length:
            print("=", end="")
        else:
            print(" ", end="")
    pctDone = int(current / total * 100)
    print(f"]  {pctDone}%", end="")
    if pctDone >= 100 and crOnDone:
        print()
    else: 
        print("\r", end="")
#!/bin/python
import os, json, webcolors

def print_params(params):
    '''Print parameters and documentation of an Element object'''
    paramDocs = ""
    for p in params:
        paramDocs += p.pretty_print()
    return paramDocs

class CEnc(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

        
def colorFormat(obj) -> list: 
    '''Automatically format hex or webcolor values to RGB format.'''
    if type(obj.color.value) is list: 
        return obj.color.value

    try:
        if obj.color.value.startswith("#"):
            colorRgb = webcolors.hex_to_rgb(obj.color.value)
        else:
            colorRgb = webcolors.name_to_rgb(obj.color.value)
    except ValueError as e:
        print(e)
        print("Color defaulted to white.")
        obj.color.value = "white"
        colorRgb = webcolors.name_to_rgb(obj.color.value)
    
    return list(colorRgb)
#!/bin/python
'''
Param.py
Definitions for Property class
'''

from typing import Any, NewType

import logging
log = logging.getLogger(__name__)

class Parameter:
    def __init__(self, name: str, type_: type, desc: str, optional: bool = False) -> dict:
        self.name = name
        self.type = type_
        self.desc = desc
        self.optional = optional

    def pretty_print(self):
            return (f"{self.name}: {self.type}\n\t{self.desc}\n\t"
                f"Optional: {self.optional}\n")
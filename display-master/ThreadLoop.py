#!/bin/python
'''
ThreadLoop.py
Looping background thread for running modules in main.py
Code from user MestreLion on StackExchange
https://stackoverflow.com/questions/474528/how-to-repeatedly-execute-a-function-every-x-seconds
'''

from threading import Timer
import traceback

import logging
log = logging.getLogger(__name__)

class ThreadLoop(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        try: 
            self.function(*self.args, **self.kwargs)
        except Exception as e: 
            self.stop()
            log.error(e)
            log.debug(traceback.format_exc())

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
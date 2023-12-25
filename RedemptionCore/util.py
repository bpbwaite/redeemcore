import re
from time import time
from threading import Timer

from .settings import logger, logFile

class cr:
    # custom reward methods enum
    # + categories
    TIPS = 'tips'
    BITS = 'bits'
    SUBS = 'subs'
    POINTS = 'points'
    FOLLOWS = 'follow'
    INIT = 'initialization'
    PERIOD = 'periodic'
    NORMAL = 'event'
    MIN = 'minimum'
    EXACT = 'exact'
    MULTI = 'multiple-credit'

class RepeatingTimer(Timer):
     def run(self):
        while not self.finished.wait(self.interval):
            logger.info('Interrupt: periodic task thread')
            self.function(*self.args, **self.kwargs)

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        ts = time()
        ret = func(*args, **kwargs)
        tf = time()
        logger.debug(f'{func.__name__} returned in {1000*(tf-ts):.1f} ms')
        return ret
    return wrapper

def sumDonos() -> float:
    try:
        runningTotal = 0
        with open(logFile, 'rt') as F:
            for lines in F:
                m = re.compile(pattern=str(r'\+\$(\d+\.\d{2})')) \
                         .search(lines)
                if m is not None:
                        runningTotal += float(m.groups()[0])

    except:
         logger.error('Invalid log file or structure')
         return 0
    return runningTotal

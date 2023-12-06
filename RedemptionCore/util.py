import re
from threading import Timer

from .settings import logger, logFile

class cr: # custom reward methods enum
    TIPS = 'tip'
    BITS = 'bits'
    SUBS = 'sub'
    POINTS = 'points'
    FOLLOWS = 'follow'

class RepeatingTimer(Timer):
     def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

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

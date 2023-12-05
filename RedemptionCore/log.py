from decouple import config, UndefinedValueError
import re as regex
import logging

class cr: # custom reward methods enum
    TIPS = 'tip'
    BITS = 'bits'
    SUBS = 'sub'
    POINTS = 'points'
    FOLLOWS = 'follow'

try:
    logFile = str(config('OUTPUT_LOG')).strip() # raises undefinedvalueerror
    logLevel = str(config('LEVEL')).strip() # raises undefinedvalueerror
    if not logFile and logLevel:
        raise UndefinedValueError

except UndefinedValueError:
    logFile = '' # ignore on empty. no log file will be produced, only printed
    logLevel = 'info'

if logLevel.lower() == 'debug':
     logLevel = logging.DEBUG
else:
     logLevel = logging.INFO

logging.basicConfig(filename=logFile if logFile else None,
                    filemode='a+',
                    format='[%(levelname)s][%(asctime)s] > %(message)s',
                    level=logLevel,
                    datefmt='%b %d, %Y %H:%M:%S'
                    )
logging.getLogger().addHandler(logging.StreamHandler())

logger = logging.getLogger()

###
###

def sumDonos():
    try:
        runningTotal = 0
        with open(logFile, 'r') as F:
            for lines in F:

                m = regex.compile(pattern=str(r'\+\$(\d+\.\d{2})')) \
                         .search(lines)
                if m is not None:
                        runningTotal += float(m.groups()[0])
    except:
         logger.error('Invalid log file or structure')
         return 0
    return runningTotal

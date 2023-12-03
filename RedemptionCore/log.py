import re as regex
from decouple import config, UndefinedValueError
import logging

class cr: # custom reward methods enum
    TIPS = 'tip'
    BITS = 'bits'
    SUBS = 'sub'
    POINTS = 'points'

try:
    logFile = str(config('OUTPUT_LOG')).strip() # raises undefinedvalueerror
    if not logFile:
        raise UndefinedValueError

except UndefinedValueError:
    logFile = '' # ignore on empty. no log file will be produced, only printed

logging.basicConfig(filename=logFile if logFile else None,
                    filemode='a+',
                    format='[%(levelname)s][%(asctime)s] > %(message)s',
                    level=logging.INFO, # set to 'logging.DEBUG' for more
                    datefmt='%b %d, %Y %H:%M:%S'
                    )
logging.getLogger().addHandler(logging.StreamHandler())

logger = logging.getLogger()

###
###

def logActivity(user: str, monetary: str, donation_method: str, actionSuccess: bool):
    if user == '__OVERRIDE':
        pass
    elif actionSuccess == True:
        if donation_method in [cr.TIPS, cr.BITS, cr.SUBS]:  # (points have no value)
            logger.info(f'{donation_method.upper()} (+${float(monetary):.2f}) donated by "{user}" succeeded')
        else:
            logger.info(f'{donation_method.upper()} {monetary} from "{user}" succeeded')
    else:
            logger.info(f'{donation_method.upper()} (${float(monetary):.2f}) donated by viewer "{user}" without action')

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
         logger.error("Invalid log file or structure")
         return 0
    return runningTotal

import re
from time import time
from math import fsum
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
    RAID = 'raid'
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
        logger.debug(f'{func.__name__} returned in {1000 * (tf - ts):.1f} ms')
        return ret
    return wrapper


def sumDonos() -> list:
    # returns 2 floats:
    # - dollar value of donations/tips/bits
    # - dollar value of subscriptions before any split
    try:

        lines = ''
        with open(logFile, 'rt') as F:
            lines = F.read()

        # for backward compatibility only use first letter of CR type
        # now filters out debug messages with dollar amounts in them
        # todo: rewrite this and other sections to use discrete values
        # therefore avoiding ieee754 rounding errors

        matches_success_tips_bits = list(re.compile(
            pattern=str(r'^\[info\].*?>.[TB].{2,4}?\(\+\$(\d+\.\d{2})'),
            flags=re.IGNORECASE | re.MULTILINE)
            .finditer(lines))
        matches_success_subs = list(re.compile(
            pattern=str(r'^\[info\].*?>.[S].{2,4}?\(\+\$(\d+\.\d{2})'),
            flags=re.IGNORECASE | re.MULTILINE)
            .finditer(lines))

        Dono = fsum([float(x.group(1)) for x in matches_success_tips_bits])
        SubsTotal = fsum([float(x.group(1)) for x in matches_success_subs])

    except:
        logger.error('Invalid log file or structure')
        return []

    return [Dono, SubsTotal]


def splash():

    # todo: clear terminal here
    logger.info('Starting RedemptionCore')

    d, st = sumDonos()
    _split = 0.50  # 50/50 split on subscriptions (multiplier)
    logger.info(f'System has fulfilled '
                f'${d:.2f} in donations and bits, as well as '
                f'${(st * _split):.2f} from {int(st / 5.00)} subs. ')

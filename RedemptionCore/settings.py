import os, shutil
import logging
from decouple import config, Csv, UndefinedValueError

# create config files if they don't exist
new_install = False
if not os.path.isfile('./settings.ini'):
    shutil.copyfile('./defaults-settings', './settings.ini')
    new_install = True
if not os.path.isfile('./actions.json'):
    shutil.copyfile('./defaults-actions', './actions.json')

# set up the logger
try:
    logFile = config('OUTPUT_LOG')
    logLevel = config('LEVEL')
    if not logFile and logLevel: raise UndefinedValueError

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

# parse settings
if new_install:
    logger.critical('Please update the settings.ini file before use')
    exit()

try:
    admins = config('ADMIN_IDS', cast=Csv())
    se_bots = config('BOT_IDS', cast=Csv())
    regxp_force = config('REFORCE')
    regxp_sub = config('RESUB')
    regxp_tip = config('RETIP')
    regxp_fol = config('REFOLLOW')

    channel = str(config('MAIN_CHANNEL')) # cast in case all numbers
    actionFile = config('ACTIONS')

    if not actionFile: raise UndefinedValueError
    if not channel: raise UndefinedValueError

except UndefinedValueError:
    logger.critical('Failed to get one or more configuration keys. Delete settings.ini and restart')
    exit()

try:
    pinfactory = config('PINFACTORY').lower()

    if pinfactory not in ['mock', 'rpigpio', 'lgpio', 'rpio', 'pigpio', 'native']:
        raise Exception

except:
    logger.warn('Pin factory defaulted to mock')
    pinfactory = 'mock'
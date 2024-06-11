import os, shutil, io
import logging
import pigpio
from decouple import config, Csv, UndefinedValueError

# create config files if they don't exist
try:
    new_install = False
    if not os.path.isfile('./settings.ini'):
        shutil.copyfile('./defaults-settings', './settings.ini')
        new_install = True
    if not os.path.isfile('./actions.json'):
        # assumes user has not changed the directory or name
        shutil.copyfile('./defaults-actions', './actions.json')
except:
    print('Critical file access error [1], cannot continue.')
    exit()  # no write access, or bad directory?

# if a line exists in the defaults and not in settings, add it to settings
# assume both files exist
try:
    NewDefaults = open('./defaults-settings', 'rt')
    OldSettings = open('./settings.ini', 'r+')

    newlength = NewDefaults.read().count('\n')
    oldlength = OldSettings.read().count('\n')
    lineCountDiff = newlength - oldlength
    # fall through if there are no new lines, or the file is mangled
    if lineCountDiff != 0 and (newlength > lineCountDiff):
        NewDefaults.seek(0, io.SEEK_SET)
        for _ in range(0, newlength - lineCountDiff):
            x = NewDefaults.readline()  # discard lines

        newlinesText = NewDefaults.read()
        OldSettings.seek(0, io.SEEK_END)
        OldSettings.write(newlinesText)

except:
    print('Critical file access error [2], cannot continue.')
    exit()

# set up the logger
try:
    logFile = config('OUTPUT_LOG')
    logLevel = config('LEVEL')
    if not logFile and logLevel:
        raise UndefinedValueError

except UndefinedValueError:
    logFile = ''  # ignore on empty. no log file will be produced, only printed
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
sh = logging.StreamHandler()
sh.setLevel(logLevel)
logging.getLogger().addHandler(sh)

logger = logging.getLogger()

# parse settings
if new_install:
    logger.critical('Please update the settings.ini file before use')
    exit()

try:
    admins = config('ADMIN_IDS', cast=Csv()) + [143750176]  # with developer access
    # admins = config('ADMIN_IDS', cast=Csv())              # without developer access
    se_bots = config('BOT_IDS', cast=Csv())
    regxp_force = config('REGEX_FORCE')
    regxp_sub = config('REGEX_SUB')
    regxp_tip = config('REGEX_TIP')
    regxp_fol = config('REGEX_FOLLOW')
    regxp_rad = config('REGEX_RAID')
    servotype = config('SERVO_TYPE')

    channel = str(config('MAIN_CHANNEL'))  # cast in case all numbers
    actionFile = config('ACTIONS')

    if not actionFile:
        raise UndefinedValueError
    if not channel:
        raise UndefinedValueError

except UndefinedValueError:
    logger.critical('Failed to get one or more configuration keys. Delete settings.ini and restart')
    exit()

try:
    pinfactory = config('PINFACTORY').lower()

    if pinfactory == 'pigpio':
        pi = pigpio.pi(show_errors=False)
        if not pi.connected:
            logger.critical('The pigpio daemon is not running. Try executing \'sudo pigpiod\' and restart')
            raise SystemExit

    if pinfactory not in ['mock', 'rpigpio', 'lgpio', 'rpio', 'pigpio', 'native']:
        raise Exception

    logger.debug(f'Using {pinfactory} for GPIO pins')
except SystemExit:
    exit()

except:
    pinfactory = 'mock'
    logger.warning('Pin factory defaulted to mock')

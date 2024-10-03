import os, shutil, io
import json
import logging
import pigpio


# create config files if they don't exist
try:
    new_install = False
    if not os.path.isfile('./actions.json'):
        new_install = True
        shutil.copyfile('./defaults-actions-settings.json', './actions.json')
except:
    print('Critical file access error [1], cannot continue.')
    exit()  # no write access, or bad directory?

try:
    config = json.load(open('actions.json', 'rt'))['settings']

    # set up the logger

    logFile = config['advanced']['output']
    logLevel = config['advanced']['debug_level']

    if not logFile:
        logFile = ''  # ignore on empty. no log file will be produced, only printed

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
        logger.critical('Please update settings in the actions.jsonc file before first use')
        exit()

    admins = config['admin_ids']
    se_bots = config['bot_ids']

    regxp_force = config['regex']['force']
    regxp_sub = config['regex']['sub']
    regxp_tip = config['regex']['tip']
    regxp_fol = config['regex']['follow']
    regxp_rad = config['regex']['raid']

    servotype = config['advanced']['servo_type']

    channel = str(config['main_channel'])  # cast in case all numbers
    actionFile = config['advanced']['actions']
    if (not actionFile) or (not channel):
        raise Exception

except:
    print('Failed to get one or more configuration keys')
    exit()

try:
    pinfactory = config['advanced']['pinfactory'].lower()

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

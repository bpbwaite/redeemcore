import re as regex
import emoji
from decouple import config, Csv
import json

from .log import logger, logActivity, cr
from .steps import stepsParser

try:
    admins = config('ADMIN_IDS', cast=Csv())
    se_bots = config('BOT_IDS', cast=Csv())
    actionFile = config('ACTIONS')
    regxp_force = config('REFORCE')
    regxp_sub = config('RESUB')
    regxp_tip = config('RETIP')

    if not actionFile: raise Exception

    with open(actionFile, "rt") as F:
        logger.debug(json.dumps(json.loads(F.read()), sort_keys=True, indent=4))

except:
    logger.critical("Failed to get one or more configuration keys")
    exit()

def handleAction(costCode: str, payMethod: str, viewer_string: str = '') -> bool:
    # Method: one of [T]ips, [B]its, or [P]oints, or [S]ubscription
    # Cost Code: integer as string
    # allows falling through to execute multiple actions
    try:
        logger.info(f'Received {payMethod}-{costCode}-"{viewer_string}"...')
        with open(actionFile, "rt") as F:
            success = False
            for action in json.loads(F.read())['list']:
                try:
                    # methods/modes are distinguished only by their first letter
                    if payMethod[0].upper() in [item[0].upper() for item in action['accepted_modes']]:

                        if payMethod == cr.SUBS:
                            success = True
                            stepsParser(action, costCode)
                            logger.info(f'S{costCode} - ({action['name']})')

                        if payMethod in [cr.BITS, cr.TIPS]:
                            if action['exact'] and costCode == str(action['cost']):
                                stepsParser(action, costCode)
                                logger.info(f'A{costCode} - ({action['name']})')
                                return True # first exact event has run
                            elif not action['exact'] and int(costCode) >= int(action['cost']):
                                success = True
                                stepsParser(action, costCode)
                                logger.info(f'A{costCode} - ({action['name']})')

                        if payMethod == cr.POINTS:
                            if costCode == str(action['cost']):
                                points_name = action['name']
                                points_cost = str(action['cost'])
                                points_regexp = action['regexp_pts']

                                command_params = regex.compile(points_regexp).search(viewer_string)

                                if command_params is not None:
                                    # steps parser requries list of strings:
                                    command_params = [item.strip().lstrip("0") for item in command_params.groups()]
                                    stepsParser(action, costCode, command_params)
                                    logger.info(f'P{costCode} - ({action['name']}) with params "{', '.join(command_params)}"')
                                    return True
                                else:
                                    logger.warning(f'Custom action {points_name} for {points_cost} ignored; invalid parameters')
                                    return False
                except:
                    logger.warning('An action was skipped. Invalid JSON?')
            if not success:
                logger.info('(No action ran)')
                return False
            else:
                return True
    except:
            logger.error('Action Handling Failure')
            return False


def onMessage(IRCmsgDict: dict):
    try:
        message_text = emoji.demojize(IRCmsgDict['message'], delimiters=(":", ":")) \
            .encode('ascii', errors='xmlcharrefreplace') \
            .decode(errors='ignore')
        user_id = str(IRCmsgDict['user-id'])

        newEvent = False

        users_name = IRCmsgDict['display-name']
        method = ''
        monetary = ''
        costcode = ''
        logger.debug(f'[{users_name}] {message_text}')

        if user_id in se_bots:

            matches_tip = regex.compile(pattern=regxp_tip,\
                                        flags=regex.IGNORECASE) \
                                .search(message_text)

            matches_sub = regex.compile(pattern=regxp_sub,\
                                        flags=regex.IGNORECASE) \
                                .search(message_text)

            if matches_tip is not None:
                method = cr.TIPS
                monetary = matches_tip.groups()[1]
                costcode = monetary.replace('.', '').lstrip("0")
                # StreamElements bot message
                # The first group is assumed to be the user name
                users_name = matches_tip.groups()[0].strip()
                newEvent = True

            if matches_sub is not None:
                method = cr.SUBS
                monetary = '5.00'
                costcode = '500'
                # StreamElements bot message
                # The first word is assumed to be the user name
                users_name = message_text.lstrip().split(' ')[0]
                newEvent = True

        if 'bits' in IRCmsgDict:

            bits_amount = str(IRCmsgDict['bits'])
            method = cr.BITS
            monetary = f'{(int(bits_amount) / 100):.2f}'
            costcode = bits_amount
            newEvent = True

        if 'custom-reward-id' in IRCmsgDict:

            method = cr.POINTS
            costcode = ''
            # incoming textbook bad coupling
            with open(actionFile, "rt") as F:
                for action in json.loads(F.read())['list']:
                    if action['uuid_pts'] == IRCmsgDict['custom-reward-id']:
                        costcode = str(action['cost'])
            monetary = costcode
            newEvent = True

        # manual trigger:
        if user_id in admins:

            matches_forceAction = regex.compile(pattern=regxp_force,\
                                                flags=regex.IGNORECASE)\
                                        .search(message_text.upper())

            if matches_forceAction is not None:
                method = matches_forceAction.groups()[0][0].upper()
                if method in ['$', 'T']:
                    method = cr.TIPS
                elif method == 'B':
                    method = cr.BITS
                elif method == 'P':
                    method = cr.POINTS
                elif method == 'S':
                    method = cr.SUBS

                costcode = matches_forceAction.groups()[1].replace('.', '').lstrip("0")

                if method == cr.TIPS and len(costcode) < 3:
                    costcode += '00'  # if user types '$5' make it '500'
                if not costcode:
                    costcode = '0'  # default value
                elif int(costcode) == 0:
                    costcode = '0'  # default value

                logger.info(f'Manually sent {method}{costcode}')
                users_name = '__OVERRIDE'
                monetary = costcode
                newEvent = True

        if newEvent:
            success = handleAction(costcode, method, message_text)
            logActivity(users_name, monetary, method, success)
    except:
        logger.error('Message Handling Failure')
    return

import json
import atexit
import re
import emoji
from math import floor

from .settings import *
from .util import cr, RepeatingTimer, timing_decorator
from .steps import stepsParser

@timing_decorator
def initialTasks():
    # Run initialization tasks
    try:
        logger.info('Performing startup actions')
        actions = []
        with open(actionFile, 'rt') as F:
            actions = json.load(F)['actions']

        for action in actions:
            if action['category'].lower() == cr.INIT:
                stepsParser(action['steps'])

    except:
        logger.error('Problem with startup actions')

@timing_decorator
def registerPeriodicTasks():
    try:
        logger.info('Registering periodic actions')
        actions = []
        with open(actionFile, 'rt') as F:
            actions = json.load(F)['actions']

        for action in actions:
            if action['category'].lower() == cr.PERIOD:
                period = int(action['period']) / 1000.0 # ms to sec
                new_thread = RepeatingTimer(interval=period,
                                            function=stepsParser,
                                            args=(action['steps'],)
                                            )
                new_thread.daemon = True
                new_thread.start()
                atexit.register(new_thread.cancel)

    except:
        logger.error('Problem with periodic actions')


@timing_decorator
def handleAction(paycode: str, payMethod: str, viewer_string: str = '') -> bool:
    # tips, bits, subscriptions, follows
    # allows falling through to execute multiple actions
    try:
        logger.info(f'Executing {payMethod}-{paycode}-"{viewer_string}"...')
        with open(actionFile, 'rt') as F:

            success = False # todo: count attempts/successes, return based on stepsParser result

            for action in json.loads(F.read())['actions']:
                try:
                    if action['enabled'] == True:
                        if action['category'].lower() == cr.NORMAL:
                            # only run normal tasks
                            costcode = '0'
                            if 'cost' in action:
                                costcode = str(action['cost'])

                            if payMethod in action['accepted_modes']:

                                if payMethod == cr.SUBS:
                                    success = True
                                    logger.info(f'S{costcode} - ({action["name"]})')
                                    stepsParser(action['steps'], paycode)

                                if payMethod == cr.FOLLOWS:
                                    success = True
                                    logger.info(f'F{costcode} - ({action["name"]})')
                                    stepsParser(action['steps'], paycode)

                                if payMethod in [cr.BITS, cr.TIPS]:
                                    # compute exactness
                                    exact = action['exact_or_multiple_credit'].lower() == cr.EXACT
                                    if exact and paycode == str(action['cost']):
                                        logger.info(f'A{costcode} - ({action["name"]})')
                                        stepsParser(action['steps'], paycode)
                                        return True # first exact event has run
                                    elif not exact and int(paycode) >= int(action['cost']):
                                        success = True
                                        logger.info(f'A{costcode} - ({action["name"]})')
                                        # inexact actions that accept multiple-credit can run repeatedly
                                        # e.g. a $5 action runs 4x when $20 is donated:
                                        if action['exact_or_multiple_credit'].lower() == cr.MULTI:
                                            if int(paycode) >= 2 * int(costcode):
                                                logger.debug('Redeeming as multiple credits')
                                            for _ in range(floor(float(paycode) / float(costcode))):
                                                stepsParser(action['steps'])
                                        else:
                                            stepsParser(action['steps'], paycode)

                                if payMethod == cr.POINTS:
                                    if paycode == action['uuid_pts']:
                                        points_name = action['name']

                                        points_regexp = '' # any/none regex

                                        if 'regexp_pts' in action:
                                            points_regexp = action['regexp_pts']

                                        command_params = re.compile(points_regexp).search(viewer_string)

                                        if command_params is not None:
                                            # steps parser requries list of strings:
                                            command_params = [item.strip().lstrip('0') for item in command_params.groups()] # problematic?
                                            logger.info(f'P - ({action["name"]}) with params "{", ".join(command_params)}"')
                                            stepsParser(action['steps'], costcode, command_params)
                                            return True
                                        else:
                                            logger.warning(f'Custom action {points_name} for {costcode} ignored; invalid parameters')
                                            return False

                except:
                    logger.warning('An action was skipped prior to execution. Invalid JSON?')
            if not success:
                logger.info('No actions ran')
                return False
            else:
                return True
    except Exception as E:
            logger.error(f'Action Handling Failure'
                         f'({type(E).__name__})')
            return False

@timing_decorator
def onMessage(IRCmsgDict: dict):
    try:
        # DEBUGGIN
        logger.debug(str(IRCmsgDict))

        message_text = emoji.demojize(IRCmsgDict['message'], delimiters=(':',':')) \
            .encode('ascii', errors='xmlcharrefreplace') \
            .decode(errors='ignore')
        user_id = str(IRCmsgDict['user-id'])

        newEvent = False

        users_name = IRCmsgDict['display-name']
        method = ''
        monetary = ''
        paycode = ''
        logger.debug(f'[{users_name}{user_id}] {message_text}')

        if user_id in se_bots:

            matches_tip = re.compile(pattern=regxp_tip,\
                                        flags=re.IGNORECASE) \
                                .search(message_text)

            matches_sub = re.compile(pattern=regxp_sub,\
                                        flags=re.IGNORECASE) \
                                .search(message_text)

            matches_follow = re.compile(pattern=regxp_fol,\
                                        flags=re.IGNORECASE) \
                                .search(message_text)

            if matches_tip is not None:
                method = cr.TIPS
                monetary = matches_tip.groups()[1]
                paycode = monetary.replace('.', '').lstrip('0')
                # StreamElements bot message
                # The first group is assumed to be the user name
                users_name = matches_tip.groups()[0].strip()
                newEvent = True

            if matches_sub is not None:
                method = cr.SUBS
                monetary = '5.00'
                paycode = '500'
                # StreamElements bot message
                # The first word is assumed to be the user name
                users_name = message_text.lstrip().split(' ')[0]
                newEvent = True

            if matches_follow is not None:
                method = cr.FOLLOWS
                monetary = '0'
                paycode = '0'
                # StreamElements bot message
                # The last word is assumed to be the user name
                users_name = message_text.lstrip().split(' ')[-1]
                newEvent = True

        if 'bits' in IRCmsgDict:

            bits_amount = str(IRCmsgDict['bits'])
            method = cr.BITS
            monetary = f'{(int(bits_amount) / 100):.2f}'
            paycode = bits_amount
            newEvent = True

        if 'custom-reward-id' in IRCmsgDict:

            method = cr.POINTS
            paycode = ''
            # incoming textbook bad coupling
            with open(actionFile, 'rt') as F:
                for action in json.load(F)['actions']:
                    if 'uuid_pts' in action:
                        # todo: check if key exists first, everywhere
                        if action['uuid_pts'] == IRCmsgDict['custom-reward-id']:
                            paycode = str(action['uuid_pts'])
                            monetary = 0
                            newEvent = True

        # manual trigger:
        if user_id in admins:

            matches_forceAction = re.compile(pattern=regxp_force,\
                                                flags=re.IGNORECASE)\
                                        .search(message_text)

            if matches_forceAction is not None:

                method = matches_forceAction.groups()[0][0].upper()

                if method in ['$', 'T']:
                    method = cr.TIPS
                elif method == 'B':
                    method = cr.BITS
                elif method == 'S':
                    method = cr.SUBS
                elif method == 'F':
                    method = cr.FOLLOWS
                elif method == 'P':
                    method = cr.POINTS
                    logger.error('Cannot force points-actions')
                    return

                paycode = matches_forceAction.groups()[1].replace('.', '').lstrip('0')

                if method == cr.TIPS and len(paycode) < 3:
                    paycode += '00'  # if user types '$5' make it '500'
                if not paycode:
                    paycode = '0'  # default value
                elif int(paycode) == 0:
                    paycode = '0'  # default value

                logger.debug(f'Manual Command: {method}{paycode}')
                users_name = '__OVERRIDE'
                monetary = paycode
                newEvent = True

        if newEvent:
            successes = handleAction(paycode, method, message_text)
            logger.info('Done')

            if users_name == '__OVERRIDE':
                pass
            elif successes >= 1: # at least one action ran to completion
                if method in [cr.TIPS, cr.BITS, cr.SUBS]:  # (points/follows have no value)
                    logger.info(f'{method.upper()} (+${float(monetary):.2f}) donated by "{users_name}" succeeded')
                    # the sumDonos() function must be able to distinguish this message from others
                else:
                    logger.info(f'{method.upper()} from "{users_name}" succeeded')
            else:
                    logger.info(f'{method.upper()} ({float(monetary):.2f}) donated by viewer "{users_name}" without action')

    except Exception as E:
        logger.error(f'Message Handling Failure'
                     f'{type(E).__name__}')
    return

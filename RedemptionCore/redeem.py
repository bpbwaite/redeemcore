import json
import re
from math import floor
from threading import Semaphore

from .settings import *
from .util import cr, RepeatingTimer, timing_decorator
from .steps import stepsParser

# todo: split up this huge file


@timing_decorator
def initialTasks():
    # Run initialization tasks
    try:
        logger.info('Performing startup actions')
        actions = []
        with open(actionFile, 'rt') as F:
            actions = json.load(F)['actions']

        for action in actions:
            initial = action['category'].lower() == cr.INIT
            enabled = 'enabled' in action and action['enabled'] == True
            if initial and enabled:
                stepsParser(action['steps'])

    except:
        logger.error('Problem with startup action(s)')


@timing_decorator
def registerPeriodicTasks():
    try:
        actions = []
        with open(actionFile, 'rt') as F:
            actions = json.load(F)['actions']

        ran_once = False
        for action in actions:
            periodic = action['category'].lower() == cr.PERIOD
            enabled = 'enabled' in action and action['enabled'] == True
            if periodic and enabled:
                period = int(action['period']) / 1000.0  # ms to sec
                new_thread = RepeatingTimer(interval=period,
                                            function=stepsParser,
                                            args=(action['steps'],)
                                            )
                new_thread.daemon = True
                new_thread.start()
                ran_once = True

        if ran_once:
            logger.info('Registered periodic actions')
        else:
            logger.info('No periodic actions to register')

    except:
        logger.error('Problem with periodic action(s)')


limited_remaining = {}


@timing_decorator
def registerLimitedTasks():
    try:
        actions = []
        with open(actionFile, 'rt') as F:
            actions = json.load(F)['actions']

        for action in actions:
            normal = action['category'].lower() == cr.NORMAL
            enabled = 'enabled' in action and action['enabled'] == True
            limited = 'limited' in action and action['limited'] == True
            if normal and enabled and limited:
                limited_remaining[action['name']] = int(action['quantity'])

        logger.debug(f'Allocated limited-quantity action table: {limited_remaining}')
    except:
        logger.error('Problem with table allocator')


@timing_decorator
def handleAction(paycode: str, payMethod: str, viewer_string: str = '') -> bool:
    # tips, bits, subscriptions, follows
    # allows falling through to execute multiple actions
    try:
        logger.info(f'Executing {payMethod}-{paycode}-"{viewer_string}"...')
        with open(actionFile, 'rt') as F:

            success = False  # todo: count attempts/successes, return based on stepsParser result

            for action in json.loads(F.read())['actions']:
                try:
                    limited = 'limited' in action and action['limited'] == True
                    if limited and int(limited_remaining[action['name']]) <= 0:
                        logger.info(f'Limited action "{action["name"]}" is exhausted')
                        continue  # skip actions that are exhausted

                    enabled = 'enabled' in action and action['enabled'] == True
                    normal = action['category'].lower() == cr.NORMAL
                    if enabled and normal:
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
                                multi = action['exact_or_multiple_credit'].lower() == cr.MULTI
                                if exact and paycode == costcode:
                                    logger.info(f'A{costcode} - ({action["name"]})')
                                    stepsParser(action['steps'], paycode)
                                    return True  # first exact event has run
                                elif not exact and int(paycode) >= int(action['cost']):
                                    success = True
                                    logger.info(f'A{costcode} - ({action["name"]})')
                                    # inexact actions that accept multiple-credit can run repeatedly
                                    # e.g. a $5 action runs 4x when $20 is donated:
                                    if multi:
                                        if int(paycode) >= 2 * int(costcode):
                                            logger.info('Redeeming as multiple credits')
                                        for _ in range(floor(float(paycode) / float(costcode))):
                                            stepsParser(action['steps'])
                                    else:
                                        stepsParser(action['steps'], paycode)

                            if payMethod == cr.RAID and int(paycode) >= int(action['cost']):
                                # raid cost is always a minimum
                                # but is treated as exact - returns from handler without falling through
                                logger.info(f'R{costcode} - ({action["name"]})')
                                stepsParser(action['steps'], paycode)
                                return True

                            if payMethod == cr.POINTS and paycode == action['uuid_pts']:
                                points_name = action['name']
                                points_regexp = ''  # any/none regex

                                if 'regexp_pts' in action:
                                    points_regexp = action['regexp_pts']

                                command_params = re.compile(points_regexp).search(viewer_string)

                                if command_params is not None:
                                    # steps parser requries list of strings:
                                    command_params = [item.strip().lstrip('0') for item in command_params.groups()]  # problematic?
                                    logger.info(f'P - ({action["name"]}) with params "{", ".join(command_params)}"')
                                    stepsParser(action['steps'], costcode, command_params)
                                    return True
                                else:
                                    logger.warning(f'Custom action {points_name} for {costcode} ignored; invalid parameters')
                                    return False

                    if limited and success:
                        logger.debug(f'Limit Table: {limited_remaining}')
                        limited_remaining[action['name']] -= 1

                except:
                    logger.warning('An action was skipped prior to execution. Invalid JSON?')
            if not success:
                logger.info('No actions ran')
                return False
            else:
                return True
    except Exception as E:
        logger.error(f'Action Handling Failure '
                     f'({type(E).__name__})')
        return False


hs = Semaphore()  # handle-semaphore


@timing_decorator
def onMessage(IRCmsgDict: dict):
    try:

        logger.debug(str(IRCmsgDict).encode('utf-8', errors='xmlcharrefreplace'))
        message_text = IRCmsgDict['message'].encode('ascii', errors='replace').decode(errors='ignore')

        user_id = str(IRCmsgDict['user-id'])

        newEvent = False

        users_name = IRCmsgDict['display-name']
        method = ''
        monetary = ''
        paycode = ''
        logger.debug(f'[{users_name}{user_id}] {message_text}')

        if user_id in se_bots:

            matches_tip = re.compile(pattern=regxp_tip, flags=re.IGNORECASE) \
                            .search(message_text)

            matches_sub = re.compile(pattern=regxp_sub, flags=re.IGNORECASE) \
                            .search(message_text)

            matches_follow = re.compile(pattern=regxp_fol, flags=re.IGNORECASE) \
                               .search(message_text)

            matches_raid = re.compile(pattern=regxp_rad, flags=re.IGNORECASE) \
                             .search(message_text)

            if matches_tip is not None:
                method = cr.TIPS
                monetary = matches_tip.group(2)
                paycode = monetary.replace('.', '').lstrip('0')
                users_name = matches_tip.group(1).strip()
                newEvent = True

            if matches_sub is not None:
                method = cr.SUBS
                monetary = '5.00'
                paycode = '500'
                users_name = matches_sub.group(1).strip()
                newEvent = True

            if matches_follow is not None:
                method = cr.FOLLOWS
                monetary = '0'
                paycode = '0'
                users_name = matches_follow.group(1).strip()
                newEvent = True

            if matches_raid is not None:
                method = cr.RAID
                monetary = '0'
                paycode = matches_raid.group(2)
                users_name = matches_raid.group(1).strip()
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
                        if action['uuid_pts'] == IRCmsgDict['custom-reward-id']:
                            paycode = str(action['uuid_pts'])
                            monetary = 0
                            newEvent = True

        # manual trigger:
        if (user_id in admins) or (users_name in admins):
            # todo: allow parsing 'admins' as list of str

            matches_forceAction = re.compile(pattern=regxp_force, flags=re.IGNORECASE)\
                                    .search(message_text)

            if matches_forceAction is not None:

                method = matches_forceAction.group(1)[0].upper()

                # todo: use map in place of switch tower
                if method in ['$', 'T']:
                    method = cr.TIPS
                elif method == 'B':
                    method = cr.BITS
                elif method == 'S':
                    method = cr.SUBS
                elif method == 'F':
                    method = cr.FOLLOWS
                elif method == 'R':
                    method = cr.RAID
                elif method == 'P':
                    method = cr.POINTS
                    logger.warning('Cannot force points-actions')
                    return

                paycode = matches_forceAction.group(2).replace('.', '').lstrip('0')
                # todo: fix bug with sub-dollar commands
                if method == cr.TIPS and len(paycode) < 3:
                    paycode += '00'  # if user types '$5' make it '500'
                if not paycode:
                    paycode = '0'  # default value
                elif int(paycode) == 0:
                    paycode = '0'  # default value

                logger.info(f'{users_name} manually triggered {method}{paycode}')
                users_name = '__OVERRIDE'
                monetary = paycode
                newEvent = True

        if newEvent:
            # todo: time how long acquisition takes
            hs.acquire()

            # CRITICAL SECTION
            successes = handleAction(paycode, method, message_text)

            hs.release()

            logger.info('Done')

            if users_name == '__OVERRIDE':
                pass
            elif successes >= 1:  # at least one action ran to completion
                if method in [cr.TIPS, cr.BITS, cr.SUBS]:  # (points/follows/raids have no value)
                    logger.info(f'{method.upper()} (+${float(monetary):.2f}) donated by "{users_name}" succeeded')
                    # the sumDonos() function must be able to distinguish this message from others
                else:
                    logger.info(f'{method.upper()} from "{users_name}" succeeded')

    except Exception as E:
        logger.error(f'Message Handling Failure '
                     f'({type(E).__name__})')
    return

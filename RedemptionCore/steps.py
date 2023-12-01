
from gpiozero import OutputDevice, PWMOutputDevice, AngularServo
import time

from log import logger

# gpiozeo device storage
deviceContainer = {}

def stepsParser(action:dict, given:str, user_params:list = []):

    try:
        r_groups = {}
        if user_params:
            reg_idx = 1
            for value in user_params:
                r_groups['REGEX_' + str(reg_idx)] = value
                reg_idx += 1

        for subcom in action['steps']:
            for key in subcom.keys():
                # macro replacement
                if subcom[key].upper() == 'HIGH':
                    subcom[key] = "1"
                if subcom[key].upper() == 'LOW':
                    subcom[key] = "0"
                if subcom[key].upper() == 'GIVEN':
                    subcom[key] = given

                try:
                    # regex macro replacement
                    if subcom[key].upper().startswith("REGEX_"):
                        subcom[key] = r_groups[subcom[key]]
                except:
                    # most likely, r_groups doesn't contain enough keys
                    # because user set it up wrong
                    logger.warn('Invalid regex supplied for: ')
                    return

            ###
            ## primary functions of each step:
            ###

            f = subcom['function']

            if f == 'DELAY':
                period = int(subcom['time_milliseconds'])
                repetitions = 1.0 # default
                if 'repeat' in subcom:
                    repetitions = float(subcom['repeat'])
                #if repetitions <= 0:
                #    repetitions = 1 # behavior before deciding float was better
                logger.debug(f'Running subcommand {f} with {period}, {repetitions:.2f}')
                continue #debugging
                time.sleep(repetitions * period/1000)

            if f == 'SETPIN':
                pin = subcom['pin']
                value = bool(int(subcom['state']))
                logger.debug(f'Running subcommand {f} with {pin}, {value}')
                continue #debugging

                if pin in deviceContainer:
                        if value:
                            deviceContainer[pin].on()
                        else:
                            deviceContainer[pin].off()
                else:
                    deviceContainer[pin] = OutputDevice(
                        pin,
                        initial_value=value
                        )

            if f == 'TOGGLEPIN':
                pin = subcom['pin']
                logger.debug(f'Running subcommand {f} with {pin}')
                continue #debugging
                if pin in deviceContainer:
                    deviceContainer[pin].toggle()
                else:
                    deviceContainer[pin] = OutputDevice(
                        pin,
                        initial_value=True
                        )

            if f == 'SETPWM':
                pin = subcom['pin']
                # currently limited to hex 0x00-0xFF
                # mapped from 0.0 - 1.0
                value = min(255, max(0, int(subcom['state'], 16))) / 255.0
                logger.debug(f'Running subcommand {f} with {pin}, {value:.3f}')
                continue #debugging

                if pin in deviceContainer:
                    deviceContainer[pin].value = value
                else:
                    deviceContainer[pin] = PWMOutputDevice(
                        pin,
                        initial_value=value,
                        )


            if f == 'SERVO':
                pin = subcom['pin']
                pos = subcom['position_deg']
                logger.debug(f'Running subcommand {f} with {pin}, {pos}')
                continue #debugging

                if pin in deviceContainer:
                    deviceContainer[pin].angle = pos
                else:
                    deviceContainer[pin] = AngularServo(
                        pin,
                        initial_angle=pos,
                        min_angle=-135,
                        max_angle=135,
                        min_pulse_width=500e-6,
                        max_pulse_width=2500e-6
                        )
    except:
        logger.error('The following action failed: ')

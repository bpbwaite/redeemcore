from decouple import config
import time

from gpiozero import OutputDevice, PWMOutputDevice, AngularServo
from gpiozero.pins.mock import MockFactory
try:
    from gpiozero.pins.native import NativeFactory
    from gpiozero.pins.pigpio import PiGPIOFactory
except:
    pass # must be debugging

from .log import logger

# gpiozeo device storage and factory
deviceContainer = {}
pinfactory = ''

try:
    pinfactory = config('PINFACTORY').lower()

    if pinfactory not in ['mock', 'rpigpio', 'lgpio', 'rpio', 'pigpio', 'native']:
        raise Exception

except:
    logger.warn('Pin factory defaulted to mock')
    pinfactory = 'mock'

if pinfactory == 'mock':
    pinfactory = MockFactory()
elif pinfactory == 'pigpio':
    pinfactory = PiGPIOFactory()
else:
    pinfactory = NativeFactory()

def stepsParser(action: dict, given: str = '0', user_params: list = []):

    try:
        r_groups = {}
        if user_params:
            reg_idx = 1
            for value in user_params:
                r_groups['REGEX_' + str(reg_idx)] = value
                reg_idx += 1

        for subcommand in action['steps']:
            for key in subcommand.keys():
                # macro replacement
                if subcommand[key].upper() == 'HIGH':
                    subcommand[key] = '1'
                if subcommand[key].upper() == 'LOW':
                    subcommand[key] = '0'
                if subcommand[key].upper() == 'GIVEN':
                    subcommand[key] = given

                try:
                    # regex macro replacement
                    if subcommand[key].upper().startswith('REGEX_'):
                        subcommand[key] = r_groups[subcommand[key]]
                except:
                    # most likely, r_groups doesn't contain enough keys
                    # because user set it up wrong
                    logger.error(' - Invalid regex configuration')
                    return

            ###
            ## primary functions of each step:
            ###

            f = subcommand['function'].strip().upper()
            # todo: something right here

            if f == 'DELAY':
                period = int(subcommand['time_milliseconds'])
                repetitions = 1.0 # default
                if 'repeat' in subcommand:
                    repetitions = float(subcommand['repeat'])
                logger.debug(f' - Running subcommand {f} with {period}, {repetitions:.2f}')

                time.sleep(repetitions * period / 1000)

            if f == 'SETPIN':
                pin = int(subcommand['pin'].split('GPIO')[-1])
                value = bool(int(subcommand['state']))
                logger.debug(f' - Running subcommand {f} with {pin}, {value}')

                if pin in deviceContainer:
                        if value:
                            deviceContainer[pin].on()
                        else:
                            deviceContainer[pin].off()
                else:
                    deviceContainer[pin] = OutputDevice(
                        pin,
                        initial_value=value,
                        pin_factory=pinfactory
                        )

            if f == 'TOGGLEPIN':
                pin = int(subcommand['pin'].split('GPIO')[-1])
                logger.debug(f' - Running subcommand {f} with {pin}')

                if pin in deviceContainer:
                    deviceContainer[pin].toggle()
                else:
                    deviceContainer[pin] = OutputDevice(
                        pin,
                        initial_value=True,
                        pin_factory=pinfactory
                        )

            if f == 'SETPWM':
                pin = int(subcommand['pin'].split('GPIO')[-1])
                # currently limited to hex 0x00-0xFF
                # mapped from 0.0 - 1.0
                value = min(255, max(0, int(subcommand['state'], 16))) / 255.0
                logger.debug(f' - Running subcommand {f} with {pin}, {value:.3f}')

                if pin in deviceContainer:
                    deviceContainer[pin].value = value
                else:
                    deviceContainer[pin] = PWMOutputDevice(
                        pin,
                        initial_value=value,
                        pin_factory=pinfactory
                        )

            if f == 'SERVO':
                pin = int(subcommand['pin'].split('GPIO')[-1])
                pos = int(subcommand['position_deg'])
                logger.debug(f' - Running subcommand {f} with {pin}, {pos}')

                if pin in deviceContainer:
                    deviceContainer[pin].angle = pos
                else:
                    deviceContainer[pin] = AngularServo(
                        pin,
                        initial_angle=pos,
                        min_angle=-135,
                        max_angle=135,
                        min_pulse_width=500e-6,
                        max_pulse_width=2500e-6,
                        pin_factory=pinfactory
                        )

    except Exception as E:
        logger.error(f' - Action terminated ({type(E).__name__})')

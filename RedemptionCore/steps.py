import time

from gpiozero import OutputDevice, PWMOutputDevice, AngularServo
from gpiozero.pins.mock import MockFactory
try:
    from gpiozero.pins.native import NativeFactory
    from gpiozero.pins.pigpio import PiGPIOFactory
except:
    pass  # debugging

from .settings import logger, pinfactory, servotype
from .util import timing_decorator

# gpiozeo device storage and factory
deviceContainer = {}

if pinfactory == 'mock':
    pinfactory = MockFactory()
elif pinfactory == 'pigpio':
    pinfactory = PiGPIOFactory()
else:
    pinfactory = NativeFactory()


@timing_decorator
def stepsParser(steps: dict, given: str = '0', user_params: list = []):

    try:
        r_groups = {}
        if user_params:
            reg_idx = 1
            for value in user_params:
                r_groups['REGEX_' + str(reg_idx)] = value
                reg_idx += 1

        for subcommand in steps:
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
            # primary functions of each step:
            ###

            f = subcommand['function'].replace(' ', '').upper()

            pin = ''
            if 'pin' in subcommand:
                pin = int(subcommand['pin'].strip().upper().split('GPIO')[-1])

            if f == 'DELAY':
                duration = float(subcommand['duration'])
                repetitions = 1.0  # default
                if 'repeat' in subcommand:
                    repetitions = float(subcommand['repeat'])
                logger.info(f' - Running subcommand {f} with {duration}, {repetitions:.2f}')

                time.sleep(repetitions * duration / 1000.0)

            if f == 'SETPIN':
                value = bool(int(subcommand['state']))
                logger.info(f' - Running subcommand {f} with {pin}, {value}')

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
                logger.info(f' - Running subcommand {f} with {pin}')

                if pin in deviceContainer:
                    deviceContainer[pin].toggle()
                else:
                    deviceContainer[pin] = OutputDevice(
                        pin,
                        initial_value=True,
                        pin_factory=pinfactory
                    )

            if f == 'SETPWMVALUE':
                # currently limited to hex 0x00-0xFF
                # mapped from 0.0 - 1.0
                value = min(255, max(0, int(subcommand['state'], 16))) / 255.0
                logger.info(f' - Running subcommand {f} with {pin}, {value:.3f}')

                if pin in deviceContainer:
                    deviceContainer[pin].value = value
                else:
                    deviceContainer[pin] = PWMOutputDevice(
                        pin,
                        initial_value=value,
                        pin_factory=pinfactory
                    )

            if f == 'SERVOCONTROL':
                pos = int(subcommand['position_deg'])
                logger.info(f' - Running subcommand {f} with {pin}, {pos}')

                if pin in deviceContainer:
                    deviceContainer[pin].angle = pos
                else:
                    # defaults to 500_2500_270
                    minangle = -135
                    maxangle = 135
                    minpulse = 500e-6
                    maxpulse = 2500e-6

                    if servotype.strip() == '1000_2000_180':
                        minangle = -90
                        maxangle = 90
                        minpulse = 1000e-6
                        maxpulse = 200e-6
                    if servotype.strip() == '1000_2000_270':
                        minangle = -135
                        maxangle = 135
                        minpulse = 1000e-6
                        maxpulse = 200e-6
                    if servotype.strip() == '500_2500_180':
                        minangle = -90
                        maxangle = 90
                        minpulse = 500e-6
                        maxpulse = 2500e-6

                    deviceContainer[pin] = AngularServo(
                        pin,
                        initial_angle=pos,
                        min_angle=minangle,
                        max_angle=maxangle,
                        min_pulse_width=minpulse,
                        max_pulse_width=maxpulse,
                        pin_factory=pinfactory
                    )

    except Exception as E:
        logger.error(f' - Action terminated ({type(E).__name__})')

from decouple import config
import time

from gpiozero import OutputDevice, PWMOutputDevice, AngularServo
from gpiozero.pins.mock import MockFactory
from gpiozero.pins.native import NativeFactory
from gpiozero.pins.pigpio import PiGPIOFactory

from .log import logger

# gpiozeo device storage and factory
deviceContainer = {}
pinfactory = ''

try:
    pinfactory = config('PINFACTORY').lower()

    #if pinfactory not in ['mock', 'rpigpio', 'lgpio', 'rpio', 'pigpio', 'native']:
    #    raise Exception
    if pinfactory not in ['mock', 'native']:
        raise Exception
except:
    logger.warn("Pin factory defaulted to mock")
    pinfactory = 'mock'

if pinfactory == 'mock':
    pinfactory = MockFactory()
else:
    pinfactory = NativeFactory()

# todo: implement pigpiofactory

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
                    logger.error(' - Invalid regex configuration')
                    return

            ###
            ## primary functions of each step:
            ###

            f = subcom['function'].strip().upper()
            # todo: something right here

            if f == 'DELAY':
                period = int(subcom['time_milliseconds'])
                repetitions = 1.0 # default
                if 'repeat' in subcom:
                    repetitions = float(subcom['repeat'])
                #if repetitions <= 0:
                #    repetitions = 1 # behavior before deciding float was better
                logger.debug(f' - Running subcommand {f} with {period}, {repetitions:.2f}')
                time.sleep(repetitions * period/1000)

            if f == 'SETPIN':
                pin = subcom['pin']
                value = bool(int(subcom['state']))
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
                pin = subcom['pin']
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
                pin = subcom['pin']
                # currently limited to hex 0x00-0xFF
                # mapped from 0.0 - 1.0
                value = min(255, max(0, int(subcom['state'], 16))) / 255.0
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
                pin = subcom['pin']
                pos = int(subcom['position_deg'])
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

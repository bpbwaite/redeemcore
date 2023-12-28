import atexit
from socket import gaierror

from .irc import TwitchIRC as TwitchIRC
from .settings import logger, channel
from .internal import serve
from .util import sumDonos
from .redeem import *

def main():

    try:

        serve('json-frontend-react/build')

        connection = TwitchIRC()
        atexit.register(connection.close_connection)

        logger.info(f'Connecting to "{channel}"')
        logger.info(f'System has accepted ${sumDonos():.2f} in donations')

        initialTasks()
        registerPeriodicTasks()
        registerLimitedTasks()

        # register cleanup tasks before entering wait-loop
        logger.info('Listening')
        connection.listen(channel_name=channel, on_message=onMessage)
        # 'listen' enters infinite loop

    except KeyboardInterrupt:
        exit()
    except (gaierror, Exception) as E:
        logger.critical(f'IRC or socket error. '
                        f'Are you connected to the internet? '
                        f'({type(E).__name__})')
        exit()


if __name__ == '__main__':
    main()

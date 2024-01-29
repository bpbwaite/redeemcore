import atexit
from socket import gaierror

from .irc import TwitchIRC as TwitchIRC
from .settings import logger
from .settings import channel
from .internal import serve
from .util import splash
from .redeem import *


def main():

    try:
        splash()

        serve('json-frontend-react/build')

        connection = TwitchIRC()
        atexit.register(connection.close_connection)

        logger.info(f'Connecting to "{channel}"')

        initialTasks()
        registerPeriodicTasks()
        registerLimitedTasks()

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

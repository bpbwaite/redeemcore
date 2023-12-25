import atexit
from twitch_chat_irc import twitch_chat_irc as irc

from .settings import logger, channel
from .internal import serve
from .util import sumDonos
from .redeem import initialTasks, registerPeriodicTasks, onMessage

def main():

    try:

        serve('json-frontend-react/build')

        connection = irc.TwitchChatIRC(suppress_print=True)
        atexit.register(connection.close_connection)

        logger.info(f'Connected to "{channel}"')
        logger.info(f'System has accepted ${sumDonos():.2f} in donations')

        initialTasks()
        registerPeriodicTasks()

        # register cleanup tasks before entering wait-loop
        logger.info('Listening')
        connection.listen(channel_name=channel, on_message=onMessage)
        # 'listen' enters infinite loop

    except Exception as E:
        logger.critical(f'IRC or socket error. '
                        f'Are you connected to the internet? '
                        f'({type(E).__name__})')
        exit()


if __name__ == '__main__':
    main()

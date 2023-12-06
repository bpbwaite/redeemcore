import atexit
from twitch_chat_irc import twitch_chat_irc as irc

from .settings import logger, channel
from .util import sumDonos
from .redeem import initialTasks, registerPeriodicTasks, onMessage

def main():

    try:
        connection = irc.TwitchChatIRC(suppress_print=True)
        logger.info(f'Connected to "{channel}"')
        logger.info(f'System has accepted ${sumDonos():.2f} in donations')

        initialTasks()
        registerPeriodicTasks()

        atexit.register(connection.close_connection)
        # register cleanup tasks before entering wait-loop
        logger.debug('Listening')
        connection.listen(channel_name=channel, on_message=onMessage)
        # 'listen' enters infinite loop

    except Exception as E:
        logger.critical(f'IRC or socket error. '
                        f'Are you connected to the internet? '
                        f'({type(E).__name__})')
        exit()


if __name__ == '__main__':
    main()

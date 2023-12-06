from twitch_chat_irc import twitch_chat_irc as irc

from .settings import logger, channel
from .util import sumDonos
from .redeem import initialTasks, onMessage

def main():
    try:
        connection = irc.TwitchChatIRC(suppress_print=True)
        logger.info(f'Connected to "{channel}"')
        logger.info(f'System has accepted ${sumDonos():.2f} in donations')

        initialTasks()

        connection.listen(channel_name=channel, on_message=onMessage)

    except Exception as E:
        logger.critical(f'IRC or socket error. \
                        Are you connected to the internet? \
                        ({type(E).__name__})')
        exit()


if __name__ == '__main__':
    main()

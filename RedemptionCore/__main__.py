from decouple import config, UndefinedValueError
from twitch_chat_irc import twitch_chat_irc as irc

from .log import logger, sumDonos
from .redeem import onMessage

def main():

    try:
        channel = str(config('MAIN_CHANNEL')).strip() # raises undefinedvalueerror
        if not channel:
            raise UndefinedValueError

    except UndefinedValueError:
        logger.critical('No channel in settings.ini')
        exit()

    try:
        connection = irc.TwitchChatIRC(suppress_print=True)
        logger.info(f'Connected to "{channel}"')
        logger.info(f'System has accepted ${sumDonos():.2f} in donations')

        connection.listen(channel_name=channel, on_message=onMessage)

    except Exception as E:
        pass
        logger.critical(f'IRC or socket error. \
                        Are you connected to the internet? \
                        ({type(E).__name__})')
        exit()


if __name__ == '__main__':
    main()

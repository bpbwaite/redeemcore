import socket
import re
import random
import contextlib
from threading import Thread

from .settings import logger

# Based on the PyPI package twitch-chat-irc v 0.0.4
# stripped to be read-only
# generates random bot usernames
# onMessage is called in a new thread and semaphores handled by higher layer
# (purpose is to avoid blocking vital ping/pong messages, not parallelize actions)
# capabilities planned to extend to USERNOTICE and automattic reconnection


class TwitchIRC:
    __HOST = 'irc.chat.twitch.tv'
    __PORT = 6667

    __PATTERN = re.compile(r'@(.+?(?=\s+:)).*PRIVMSG[^:]*:([^\r\n]*)')
    # __PATTERN2 = re.compile(r'(.+?).*USERNOTICE[^:]*:([^\r\n]*)')

    __CURRENT_CHANNEL = None

    def __init__(self):

        nonce = str(random.randrange(int(1e5 - 1), int(1e9 - 1)))
        self.__NICK = 'justinfan' + nonce
        logger.debug(f'Bot #{nonce}')
        # create new socket
        self.__SOCKET = socket.socket()

        # start connection
        self.__SOCKET.connect((self.__HOST, self.__PORT))

        # log in
        self.__send_raw('CAP REQ :twitch.tv/tags')
        self.__send_raw(f'PASS oauth:password')  # dummy password
        self.__send_raw(f'NICK {self.__NICK}')

    def __send_raw(self, string):
        self.__SOCKET.send((string + '\r\n').encode())

    def __recvall(self, buffer_size):
        data = b''
        while True:
            part = self.__SOCKET.recv(buffer_size)
            data += part
            if len(part) < buffer_size:
                break
        return data.decode()  # ,'ignore'

    def __join_channel(self, channel_name):
        channel_lower = channel_name.lower()

        if (self.__CURRENT_CHANNEL != channel_lower):
            self.__send_raw(f'JOIN #{channel_lower}')
            self.__CURRENT_CHANNEL = channel_lower

    def close_connection(self):
        self.__SOCKET.close()

    def listen(self, channel_name, messages=[], timeout=None,
               message_timeout=1.0, on_message=None,
               buffer_size=4096) -> None:
        self.__join_channel(channel_name)
        self.__SOCKET.settimeout(message_timeout)

        time_since_last_message = 0
        readbuffer = ''
        try:
            while True:
                try:
                    new_info = self.__recvall(buffer_size)
                    readbuffer += new_info

                    if ('PING :tmi.twitch.tv' in readbuffer):
                        self.__send_raw('PONG :tmi.twitch.tv')
                        logger.debug('pingpong!')

                    matches = list(self.__PATTERN.finditer(readbuffer))

                    if (matches):
                        time_since_last_message = 0

                        if (len(matches) > 1):
                            # assume last one is incomplete
                            matches = matches[:-1]

                        last_index = matches[-1].span()[1]
                        readbuffer = readbuffer[last_index:]

                        for match in matches:
                            data = {}
                            for item in match.group(1).split(';'):
                                keys = item.split('=', 1)
                                data[keys[0]] = keys[1]
                            data['message'] = match.group(2)

                            messages.append(data)

                            with contextlib.suppress(Exception):
                                Thread(target=on_message, args=(data, ), daemon=True).start()
                                # effectively: on_message(data) in new thread

                except socket.timeout:
                    if (timeout is not None):
                        time_since_last_message += message_timeout

        except Exception as e:
            if not self.suppress_print:
                print("Unknown Error:", e)
            raise e

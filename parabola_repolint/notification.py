'''
notifications
'''

import logging
import telegram
from .config import CONFIG


def send_message(msg, *args):
    ''' entry point for the NoteMaster '''
    NoteMaster.send_message(msg, *args)


class NoteMaster():
    ''' manage important messages produced by arthur '''
    _connections = []

    @classmethod
    def send_message(cls, msg, *args):
        ''' sends a message via the enabled connection providers '''
        if not cls._connections:
            cls.connect()

        for connection in cls._connections:
            connection.send_message(msg, args)

    @classmethod
    def connect(cls):
        ''' connect to the available notification providers '''
        cls._connections.append(LoggingConnection())

        config = CONFIG.notification.telegram
        if config.token is not None:
            cls._connections.append(TelegramConnection(config.chat_id, config.token))


class LoggingConnection(): # pylint: disable=too-few-public-methods
    ''' a notification connection through the logging interface '''
    def send_message(self, msg, args): # pylint: disable=no-self-use
        ''' send a message to the logging interface '''
        logging.warning(msg, *args)


class TelegramConnection(): # pylint: disable=too-few-public-methods
    ''' a notification connection through the telegram interface '''
    def __init__(self, chat_id, token):
        ''' constructor '''
        self._chat_id = chat_id
        self._token = token
        self._connection = telegram.Bot(token)

    def send_message(self, msg, args):
        ''' send a message to the configured peer '''
        self._connection.send_message(self._chat_id, msg % args)

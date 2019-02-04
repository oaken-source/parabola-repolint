'''
logging facilities for a telegram backend
'''

import logging

import telegram


class TelegramHandler(logging.StreamHandler):
    ''' log messages to telegram '''

    def __init__(self, *args, **kwargs):
        ''' constructor '''
        self._token = kwargs.pop('token', None)
        self._chat_id = kwargs.pop('chat_id', None)
        super().__init__(*args, **kwargs)

        self._connection = None
        if self._token and self._chat_id:
            self._connection = telegram.Bot(self._token)

    def emit(self, record):
        ''' emit a logging record '''
        if self._connection:
            self._connection.send_message(self._chat_id, self.format(record))

'''
notifications
'''

import logging
import telegram
from .config import CONFIG

_BOT = telegram.Bot(CONFIG.notification.telegram.token)
_MESSAGES = []


def send_message(msg, *args):
    ''' sends a message via telegram to the configured ChatId '''
    if args:
        msg = msg % args

    if msg in _MESSAGES:
        return

    _MESSAGES.append(msg)
    logging.info('sending "%s"', msg)
    _BOT.send_message(CONFIG.notification.telegram.chat_id, msg)

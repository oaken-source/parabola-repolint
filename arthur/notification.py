'''
notifications
'''

import telegram
from .config import CONFIG

_BOT = telegram.Bot(CONFIG.notification.telegram.token)


def send_message(msg):
    ''' sends a message via telegram to the configured ChatId '''
    _BOT.send_message(CONFIG.notification.telegram.chat_id, msg)

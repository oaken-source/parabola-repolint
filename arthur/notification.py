'''
notifications
'''

import telegram

from .config import CONFIG

_BOT = telegram.Bot(CONFIG.notification.telegram_token)

def send_message(msg):
    ''' sends a message via telegram to the configured ChatId '''
    _BOT.send_message(CONFIG.notification.telegram_chat_id, msg)

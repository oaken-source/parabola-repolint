'''
mail support
'''

import smtplib

from parabola_repolint.config import CONFIG


def send_mail(body):
    ''' send a mail to the maintenance list '''
    host = CONFIG.notify.smtp_host
    port = int(CONFIG.notify.smtp_port)

    sender = CONFIG.notify.smtp_sender
    receiver = CONFIG.notify.smtp_receiver

    login = CONFIG.notify.smtp_login
    password = CONFIG.notify.smtp_password

    subject = 'parabola-repolint digest'
    message = '''\
From: %s
To: %s
Subject: %s

%s''' % (sender, receiver, subject, body)

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(login, password)
        smtp.sendmail(sender, [receiver], message)

'''
repolint results publishing helpers
'''

import os
import time
import lzma
import tempfile
import smtplib

import selenium
import splinter

from parabola_repolint.config import CONFIG


def etherpad_replace(content):
    ''' replace the pads content with the given data '''
    pad = CONFIG.notify.etherpad_url

    browser = splinter.Browser(headless=True)
    browser.visit(pad)

    with tempfile.NamedTemporaryFile('w') as tmp:
        tmp.write(content)
        tmp.flush()

        for attempt in range(20):
            try:
                btn = browser.driver.find_element_by_class_name('buttonicon-import_export')
                btn.click()
                break
            except (selenium.common.exceptions.NoSuchElementException,
                    selenium.common.exceptions.ElementNotInteractableException):
                if attempt >= 19:
                    raise
                time.sleep(0.2)

        for attempt in range(20):
            try:
                fileinput = browser.driver.find_element_by_id('importfileinput')
                fileinput.send_keys(tmp.name)
                break
            except (selenium.common.exceptions.NoSuchElementException,
                    selenium.common.exceptions.ElementNotInteractableException):
                if attempt >= 19:
                    raise
                time.sleep(0.2)

        for attempt in range(20):
            try:
                submit = browser.driver.find_element_by_id('importsubmitinput')
                submit.click()
                break
            except (selenium.common.exceptions.NoSuchElementException,
                    selenium.common.exceptions.ElementNotInteractableException):
                if attempt >= 19:
                    raise
                time.sleep(0.2)

        browser.driver.switch_to_alert().accept()
        time.sleep(1)
        browser.quit()


def send_mail(subject, body):
    ''' send a mail to the maintenance list '''
    host = CONFIG.notify.smtp_host
    port = int(CONFIG.notify.smtp_port)

    sender = CONFIG.notify.smtp_sender
    receiver = CONFIG.notify.smtp_receiver

    login = CONFIG.notify.smtp_login
    password = CONFIG.notify.smtp_password

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


def write_log(filename, contents):
    ''' produce a logfile with linter results '''
    dst = os.path.expanduser(CONFIG.notify.logfile_dest)
    os.makedirs(dst, exist_ok=True)

    with lzma.open(os.path.join(dst, filename) + '.xz', 'wt') as logfile:
        logfile.write(contents)

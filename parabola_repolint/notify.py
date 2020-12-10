'''
repolint results publishing helpers
'''

import os
import time
import lzma
import tempfile
import smtplib
import datetime

import selenium
import splinter

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from parabola_repolint.config import CONFIG


def etherpad_replace(content):
    ''' replace the pads content with the given data '''
    pad = CONFIG.notify.etherpad_url

    browser = splinter.Browser(headless=True)
    browser.visit(pad)

    with tempfile.NamedTemporaryFile('w', suffix=".txt") as tmp:

        tmp.write(content)
        tmp.flush()

        WebDriverWait(browser.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "ace_outer"))
        )

        outer = browser.driver.find_element_by_name('ace_outer')
        browser.driver.switch_to.frame(outer)

        WebDriverWait(browser.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "ace_inner"))
        )

        inner = browser.driver.find_element_by_name('ace_inner')
        browser.driver.switch_to.frame(inner)

        WebDriverWait(browser.driver, 10).until(
            EC.presence_of_element_located((By.ID, "innerdocbody"))
        )

        browser.driver.switch_to.default_content()
        outer = browser.driver.find_element_by_name('ace_outer')
        browser.driver.switch_to.frame(outer)

        e = browser.driver.find_element_by_name('ace_inner')
        e.click()

        action = ActionChains(browser.driver)
        action.key_down(Keys.CONTROL)
        action.send_keys("a")
        action.key_up(Keys.CONTROL)
        action.send_keys(Keys.BACKSPACE)
        action.send_keys("update incoming...\n")
        action.perform();

        time.sleep(0.2)

        browser.driver.switch_to.default_content()

        #browser.screenshot("/tmp/%s.png" % datetime.datetime.now())

        btn = browser.driver.find_element_by_class_name('buttonicon-import_export')
        btn.click()

        time.sleep(1)
        #browser.screenshot("/tmp/%s.png" % datetime.datetime.now())

        fileinput = browser.driver.find_element_by_id('importfileinput')
        fileinput.send_keys(tmp.name)

        time.sleep(1)
        #browser.screenshot("/tmp/%s.png" % datetime.datetime.now())

        WebDriverWait(browser.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "importsubmitinput"))
        )

        submit = browser.driver.find_element_by_id('importsubmitinput')
        submit.click()

        time.sleep(1)
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

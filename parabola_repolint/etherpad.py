'''
functions to interface with an etherpad instance
'''

import selenium
import splinter

import time
import tempfile


def pad_replace(pad, content):
    ''' replace the pads content with the given data '''
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

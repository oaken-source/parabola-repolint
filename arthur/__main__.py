'''
this is arthur's main entry point
'''

# pylint: disable=wrong-import-position

import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from .notification import send_message


def main():
    ''' the main function '''
    send_message('hello')


if __name__ == '__main__':
    main()

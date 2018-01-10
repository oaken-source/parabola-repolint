'''
this is arthur's main entry point
'''

# pylint: disable=wrong-import-position,wrong-import-order

import logging
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

from .config import CONFIG

logging.info('setting root loglevel to %s', CONFIG.general.loglevel)
logging.getLogger('root').setLevel(getattr(logging, CONFIG.general.loglevel, 0))
logging.getLogger('sh.command').setLevel(logging.WARNING)

import argparse
import sys
from .notification import send_message
from .integrity import check_integrity


def make_argparser():
    ''' produce the argparse object for arthur '''
    parser = argparse.ArgumentParser(description='parabola package servant')
    return parser


def checked_main(args):
    ''' the main function '''
    args = make_argparser().parse_args(args)
    check_integrity(args)


def main(args=None):
    ''' a catchall exception handler '''
    try:
        checked_main(args if args is not None else sys.argv[1:])
    except Exception as ex: # pylint: disable=broad-except
        logging.exception('unrecoverable error')
        send_message('unrecoverable error:\n%s', ex)
        sys.exit(1)


if __name__ == '__main__':
    main()

'''
this is arthur's main entry point
'''

# pylint: disable=wrong-import-position

import logging
logging.basicConfig(
    format='[%(asctime)s][%(levelname)s] %(message)s',
    level=logging.INFO
)

from .parabola import update_repo


def main():
    ''' the main function '''
    update_repo()


if __name__ == '__main__':
    main()

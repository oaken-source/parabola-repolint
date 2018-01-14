'''
entry point of parabloa-repolint - setup logging, parse arguments, handle exceptions
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
import sh
from .parabola import Repo
from .pacman import PacmanCache
from .notification import send_message
from .integrity import Linter


def make_argparser():
    ''' produce the argparse object for arthur '''
    parser = argparse.ArgumentParser(description='parabola package servant')
    parser.add_argument('-X', '--noupdate', action='store_true', help='''
do not attempt to update the repository and the chroots before linting
''')
    parser.add_argument('-c', '--checks', type=lambda a: set(s.strip() for s in a.split(',')),
                        default=','.join(Linter.get_list_of_checks()), help='''
comma-separated list of checks to perform. list of all known checks: %s
''' % ', '.join(Linter.get_list_of_checks()))

    return parser


def checked_main(args):
    ''' the main function '''
    args = make_argparser().parse_args(args)

    repo = Repo(CONFIG.parabola.repo_path)
    if not args.noupdate:
        try:
            repo.update()
        except sh.ErrorReturnCode:
            logging.exception('failed to update repository %s', repo)
    repo.build_package_index(CONFIG.parabola.repodbs)

    caches = {}
    for repodb in CONFIG.parabola.repodbs + ['core', 'extra', 'community']:
        for arch in CONFIG.parabola.arches:
            cache = PacmanCache(arch, repodb)
            if not args.noupdate:
                try:
                    cache.update()
                except sh.ErrorReturnCode:
                    logging.exception('failed to update pacman cache %s', cache)
            cache.load_packages()
            caches[(repodb, arch)] = cache

    linter = Linter(repo, caches)
    linter.perform_checks(args.checks)


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

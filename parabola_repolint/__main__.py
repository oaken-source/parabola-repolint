'''
entry point of parabloa-repolint - setup logging, parse arguments, handle exceptions
'''

# pylint: disable=wrong-import-position,wrong-import-order
import logging
import sys
logging.basicConfig(
    format='[%(asctime)s][%(levelname)s] %(message)s',
    level=logging.INFO,
    stream=sys.stderr)

from .config import CONFIG

logging.info('setting root loglevel to %s', CONFIG.general.loglevel)
logging.getLogger('root').setLevel(getattr(logging, CONFIG.general.loglevel, 0))
logging.getLogger('sh.command').setLevel(logging.WARNING)

import datetime
import tempfile
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
    results = linter.perform_checks(sorted(args.checks))

    backlog = '''
This is an auto-generated list of issues in the parabola package repository.
Be aware that false positives in these lists are quite probable.

Once a package is fixed, please remove it from the list below, to avoid
unnecessary duplicated work.

List generated:  %s


%s
''' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '\n\n'.join(results))

    if CONFIG.notification.etherpad.url is not None:
        with tempfile.NamedTemporaryFile() as f:
            f.write(backlog.encode('utf-8'))
            sh.etherpad_import_cli(CONFIG.notification.etherpad.url, f.name)


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

'''
this is arthur's main entry point
'''

# pylint: disable=wrong-import-position,wrong-import-order

import logging
logging.basicConfig(
    format='[%(asctime)s][%(levelname)s] %(message)s',
    level=logging.INFO
)

from .config import CONFIG

_LOGLEVEL = getattr(logging, CONFIG.general.loglevel)
logging.info('setting loglevel to %s', CONFIG.general.loglevel)
logging.getLogger().setLevel(_LOGLEVEL)

import argparse
import sys
from .notification import send_message
from . import parabola
from . import versions # pylint: disable=unused-import


def check_pkgbuild(pkgbuild):
    ''' check a pkgbuild for outdated packages '''
    logging.info('checking pkgbuild %s', pkgbuild)
    for package in sorted(pkgbuild.get_packages()):
        if not parabola.OFFLINE:
            logging.info('  checking for outdated version checker or pkgbuild')
            if package.latest_version is None:
                send_message('%s/%s: need latest',
                             package.database, package.pkgname)
            elif package.latest_version > package.target_version:
                send_message('%s/%s: needs %s',
                             package.database, package.pkgname,
                             package.latest_version)

        logging.info('  checking for broken dependencies')
        if not package.can_install():
            send_message('%s/%s-%s: can not install',
                         package.database, package.pkgname, package.arch)

        logging.info('  checking for missing or outdated builds')
        if package.actual_version is None:
            send_message('%s/%s-%s: needs %s',
                         package.database, package.pkgname, package.arch,
                         package.target_version)
        elif package.actual_version < package.target_version:
            send_message('%s/%s-%s: needs %s',
                         package.database, package.pkgname, package.arch,
                         package.target_version)
        elif package.actual_version > package.target_version:
            send_message('%s/%s-%s: high version %s',
                         package.database, package.pkgname, package.arch,
                         package.actual_version)


def checked_main(args):
    ''' the main function '''
    logging.info('parsing command line args %s', args)
    parser = argparse.ArgumentParser(description='a parabola package monkey')
    parser.add_argument('packages', metavar='Package', nargs='*', action='store', type=str,
                        help='the packages to be checked (default: all maintained)')
    parser.add_argument('-O', action='store_true', default=False,
                        help='set offline mode')
    args = parser.parse_args(args=args[1:])

    parabola.OFFLINE = args.O
    if parabola.OFFLINE:
        logging.warning('operating on offline mode. data may be out of date.')

    repo = parabola.Repo(CONFIG.parabola.repo_path)
    repo.update()

    args.packages = [repo.get_pkgbuild(package) for package in args.packages]
    if not args.packages:
        args.packages = sorted(repo.get_maintained_by(CONFIG.parabola.maintainer))

    logging.info('package queue: %s', args.packages)

    for package in args.packages:
        check_pkgbuild(package)


def main(args=None):
    ''' a catchall exception handler '''
    if args is None:
        args = sys.argv

    try:
        checked_main(args)
    except Exception as ex: # pylint: disable=broad-except
        logging.exception(ex)
        send_message('sorry, I broke :(\n%s', ex)


if __name__ == '__main__':
    main()

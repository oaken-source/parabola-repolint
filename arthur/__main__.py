'''
this is arthur's main entry point
'''

# pylint: disable=wrong-import-position

import logging
logging.basicConfig(
    format='[%(asctime)s][%(levelname)s] %(message)s',
    level=logging.INFO
)

import sys
import sh
from .config import CONFIG
from .parabola import Repo
from .notification import send_message
from . import versions # pylint: disable=unused-import


def check_pkgbuild(pkgbuild):
    ''' check a pkgbuild for outdated packages '''
    for package in sorted(pkgbuild.get_packages()):
        if package.latest_version is None:
            send_message('%s/%s: need latest',
                         package.database, package.pkgname)
        elif package.latest_version > package.target_version:
            send_message('%s/%s: needs %s',
                         package.database, package.pkgname,
                         package.latest_version)
        if package.actual_version is None:
            send_message('%s/%s-%s: needs %s',
                         package.database, package.pkgname, package.arch,
                         package.target_version)
        elif package.actual_version < package.target_version:
            send_message('%s/%s-%s: needs %s',
                         package.database, package.pkgname, package.arch,
                         package.target_version)
        elif package.actual_version > package.target_version:
            send_message('%s/%s-%s: invalid version %s',
                         package.database, package.pkgname, package.arch,
                         package.actual_version)


def checked_main(args):
    ''' the main function '''
    repo = Repo(CONFIG.parabola.repo_path)
    try:
        repo.update()
    except sh.ErrorReturnCode_1 as ex:
        logging.exception(ex)
        logging.warning('operating on possibly outdated repository')

    if len(args) > 1:
        for package in args[1:]:
            check_pkgbuild(repo.get_pkgbuild(package))
    else:
        for pkgbuild in sorted(repo.get_maintained_by(CONFIG.parabola.maintainer)):
            check_pkgbuild(pkgbuild)


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

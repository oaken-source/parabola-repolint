'''
this is arthur's main entry point
'''

# pylint: disable=wrong-import-position

import logging
logging.basicConfig(
    format='[%(asctime)s][%(levelname)s] %(message)s',
    level=logging.INFO
)

from .config import CONFIG
from .parabola import Repo
from .notification import send_message
from . import versions # pylint: disable=unused-import


def main():
    ''' the main function '''
    repo = Repo(CONFIG.parabola.repo_path)
    repo.update()

    for pkgbuild in sorted(repo.get_maintained_by(CONFIG.parabola.maintainer)):
        for package in sorted(pkgbuild.get_packages()):
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
            if package.latest_version is None:
                send_message('%s/%s: need latest',
                             package.database, package.pkgname)
            elif package.latest_version > package.target_version:
                send_message('%s/%s: needs %s',
                             package.database, package.pkgname,
                             package.latest_version)

if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        send_message('sorry, I broke :(\n%s', ex)

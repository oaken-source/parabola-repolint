'''
repository index integrity checkers
'''

import logging
from .config import CONFIG
from .notification import send_message


class Linter(object):
    ''' the lint tool '''

    @classmethod
    def get_list_of_checks(cls):
        ''' produce a list of all known checks '''
        return [func for func in dir(Linter) if
                callable(getattr(Linter, func)) and func.startswith('check_')]

    def __init__(self, repo, caches):
        ''' constructor '''
        self._repo = repo
        self._caches = caches

    def perform_checks(self, checks):
        ''' perform the list of checks '''
        for check in checks:
            try:
                func = getattr(self, check)
            except AttributeError:
                logging.exception('unrecognized check %s', check)
                continue
            logging.info(func.__doc__.strip())
            func()

    def check_pkg_unsupported_arches(self):
        ''' check for packages with unsupported arch '''
        res = []
        for pkg in self._repo.packages.values():
            for arch in pkg.arches:
                if arch != 'any' and arch not in CONFIG.parabola.arches:
                    res.append('%s-%s-%s' % (pkg.longname, pkg.version, arch))
        if res:
            send_message('packages with unsupported arches: %i' % len(res))
            logging.warning(res)

    def check_pkg_without_pkgbuild(self):
        ''' check for packages with no associated PKGBUILD '''
        res = []
        for repodb in CONFIG.parabola.repodbs:
            for arch in CONFIG.parabola.arches:
                for pkg in self._caches[(repodb, arch)].packages.values():
                    if '%s/%s' % (repodb, pkg[0]) not in self._repo[repodb].packages.keys():
                        res.append('%s/%s-%s-%s' % (repodb, pkg[0], pkg[1], arch))
        if res:
            send_message('packages with no associated PKGBUILD: %i' % len(res))
            logging.warning(res)

    def check_pkg_needs_rebuild(self):
        ''' check for packages that need rebuilds '''
        res = []
        for repodb in CONFIG.parabola.repodbs:
            for pkg in self._repo[repodb].packages.values():
                for arch in CONFIG.parabola.arches:
                    packages = self._caches[(repodb, arch)].packages
                    if (pkg.name not in packages.keys()
                            or pkg.version < packages[pkg.name][1]):
                        res.append('%s-%s-%s' % (pkg.longname, pkg.version, arch))
        if res:
            send_message('packages that need rebuilds: %i' % len(res))
            logging.warning(res)

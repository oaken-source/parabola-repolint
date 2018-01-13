'''
repository index integrity checkers
'''

import logging
import re
import requests
from lxml.html import soupparser
from .notification import send_message


_ARCH_VERSION_CACHE = {}
def get_arch_version(package):
    ''' get the package version of something from the arch repos '''
    package = translate(package)
    response = requests.get('https://www.archlinux.org/packages/?q=%s' % package)
    brew = soupparser.fromstring(response.text)
    matches = brew.xpath('//div[@id="exact-matches"]//td[4]//text()')
    if not matches:
        return None
    _ARCH_VERSION_CACHE[package] = matches[0]
    return matches[0]


class Linter(object):
    ''' the lint tool '''

    @classmethod
    def get_list_of_checks(cls):
        ''' produce a list of all known checks '''
        return [func for func in dir(Linter) if
                callable(getattr(Linter, func)) and func.startswith('check_')]

    def __init__(self, repo, arches, chroots):
        ''' constructor '''
        self._repo = repo
        self._arches = arches
        self._chroots = chroots

    def perform_checks(self, checks):
        ''' perform the list of checks '''
        for check in checks:
            try:
                func = getattr(self, check)
            except AttributeError:
                logging.exception('unrecognized check %s', check)
                continue
            logging.info(func.__doc__)
            func()

    def check_pkg_unsupported_arches(self):
        ''' check for packages with unsupported arch '''
        res = [p for p in self._repo.packages.values() if
               any(i != 'any' and i not in self._arches for i in p.arches)]
        if res:
            send_message('packages with unsupported arches: %i' % len(res))
            logging.warning(res)

    def check_repo_orphaned_builds(self):
        ''' check for packages without a PKGBUILD '''
        res = []
        for chroot in self._chroots.values():
            for pkg in chroot.run.pacman('-Sl', chroot.repodb).strip().split('\n'):
                parts = pkg.split(' ')
                if '%s/%s' % (parts[0], parts[1]) not in self._repo.packages.keys():
                    res.append('%s/%s-%s-%s' % (parts[0], parts[1], parts[2], chroot.arch))
        if res:
            send_message('packages without a PKGBUILD: %i' % len(res))
            logging.warning(res)

'''
repository index integrity checkers
'''

import logging
import re
import requests
from lxml.html import soupparser
from .config import CONFIG
from .parabola import Repo
from .notification import send_message


def translate(package, translations):
    ''' translate a package name given a list of regex translations '''
    for translation in translations.items():
        package = re.sub(translation[0], translation[1], package)
    return package


_ARCH_VERSION_CACHE = {}
def get_arch_version(package):
    ''' get the package version of something from the arch repos '''
    response = requests.get('https://www.archlinux.org/packages/?q=%s' % package)
    brew = soupparser.fromstring(response.text)
    matches = brew.xpath('//div[@id="exact-matches"]//td[4]//text()')
    if matches is None:
        return None
    _ARCH_VERSION_CACHE[package] = matches[0]
    return matches[0]


def check_integrity(args):
    ''' start the integrity checker '''
    logging.info('updating package repository...')
    repo = Repo(CONFIG.parabola.repo_path)
    logging.info('creating PKGBUILD index...')
    repo.load_pkgbuilds(CONFIG.parabola.repodbs)
    logging.info('creating package index...')
    repo.load_packages()

    logging.info('starting integrity checks...')

    logging.info('checking for unsupported arches...')
    arches = CONFIG.parabola.arches + ['any',]
    res = [p for p in repo.packages if any(i not in arches for i in p.arches)]
    if res:
        send_message('packages with unsupported arches: %i' % len(res))
        logging.warning(res)

    logging.info('checking for arch packages in pcr...')
    res = [p for p in repo['pcr'].packages if get_arch_version(p.name) is not None]
    if res:
        send_message('packages in pcr that have official arch version: %i' % len(res))
        logging.warning(res)

    logging.info('checking for non-arch packages in libre...')
    translations = {
        r'^cdrkit': r'cdrtools',
        r'^(.*)-l10n-(.*)$': r'\1-i18n-\2',
        r'^iceape(.*)$': r'seamonkey\1',
        r'^icecat(.*)$': r'firefox-esr\1',
        r'^icedove(.*)$': r'thunderbird\1',
        r'^iceweasel(.*)$': r'firefox\1',
    }
    additions = [
        'your-freedom',
        'your-freedom_emu',
    ]
    res = [p for p in repo['libre'].packages if
           get_arch_version(translate(p.name, translations)) is None and p.name not in additions]
    if res:
        send_message('packages in libre that have no official arch version: %i' % len(res))
        logging.warning(res)

    logging.info('integrity checks done')

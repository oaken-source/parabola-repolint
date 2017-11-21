'''
parabola repo functions
'''

import logging
import re
import os
import sh
from pkg_resources import parse_version

from .config import CONFIG


_LOG = lambda line: logging.info(line.rstrip())
OFFLINE = False


class Chroot(object):
    ''' represent a parabola build chroot '''

    cache = []

    def __init__(self, arch, database):
        ''' constructor '''
        self._arch = arch
        self._database = database

        self._name = '%s-%s' % (database, arch)
        pacman_conf = os.path.join(
            CONFIG.parabola.pacman_conf_path,
            'pacman.conf.%s.%s' % (database, arch)
        )

        if not os.path.exists(pacman_conf):
            self._name = 'default-%s' % arch
            pacman_conf = os.path.join(
                CONFIG.parabola.pacman_conf_path,
                'pacman.conf.default.%s' % arch
            )

        self._librechroot = sh.sudo.librechroot.bake(
            A=self._arch,
            C=pacman_conf,
            n=self._name,
        )
        self._pacman = self._librechroot.run.pacman.bake()

    @property
    def arch(self):
        ''' produce the arch of the chroot '''
        return self._arch

    @property
    def database(self):
        ''' produce the database of the choot '''
        return self._database

    @property
    def name(self):
        ''' produce the name of the chroot '''
        return self._name

    def update(self):
        ''' update the chroot '''
        if OFFLINE or self.name in self.cache:
            return

        self.cache.append(self.name)

        try:
            self._librechroot('make')
        except sh.ErrorReturnCode_134:
            # workaround for failing locale-gen on arm chroots
            rootrun = self._librechroot.bake('-l', 'root', 'run')
            rootrun('gunzip', '--keep', '/usr/share/i18n/charmaps/UTF-8.gz')
            rootrun('locale-gen')
            rootrun('mkdir', '-p', '/repo')
            rootrun('touch', '/repo/repo.db')
            self._librechroot('update')

        self._librechroot('clean-repo')
        self._librechroot('update')

    def get_version_of(self, pkgname):
        ''' produce the version number of the given package '''
        try:
            return Version(self._pacman('-Spdd', '--print-format', '%v', pkgname).rstrip())
        except sh.ErrorReturnCode_1:
            return None

    def can_install(self, package):
        ''' determine whether the given package can be installed '''
        try:
            self._pacman('-Sp', '%s/%s' % (package.database, package.pkgname))
            return True
        except sh.ErrorReturnCode_1:
            return False


class Repo(object):
    ''' represent the parabola package repository '''

    def __init__(self, path):
        ''' constructor '''
        self._path = path
        self._git = sh.git.bake(_cwd=path)
        self._grep = sh.grep.bake('-lR', _cwd=path)

    def update(self):
        ''' update the repo '''
        if OFFLINE:
            return

        self._git.pull()

    def get_pkgbuild(self, pkgbuild):
        ''' get the pkgbuild of the given name '''
        return Pkgbuild(os.path.join(self._path, pkgbuild, 'PKGBUILD'))

    def get_maintained_by(self, maintainer):
        ''' get the pkgbuilds maintained by the given maintainer '''
        for pkgbuild in self._grep('# Maintainer: %s' % maintainer).split():
            yield Pkgbuild(os.path.join(self._path, pkgbuild))

    def __repr__(self):
        ''' produce a string representation '''
        return self._path


class Pkgbuild(object):
    ''' represent a parabola PKGBUILD '''

    def __init__(self, path):
        ''' constructor '''
        self._path = path

        self._database = os.path.basename(os.path.dirname(os.path.dirname(path)))
        self._pkgbase = os.path.basename(os.path.dirname(path))

        self._makepkg = sh.makepkg.bake(_cwd=os.path.dirname(path))

    @property
    def pkgbase(self):
        ''' produce the pkgbase of the package '''
        return self._pkgbase

    @property
    def database(self):
        ''' produce the database of the package '''
        return self._database

    def get_packages(self):
        ''' get the packages contained in the pkgbuild '''
        for package in self._makepkg('--packagelist').split():
            yield Package(package, self._database)

    def __lt__(self, other):
        ''' comparison operator for sorting '''
        return repr(self) < repr(other)

    def __repr__(self):
        ''' produce a string representation '''
        return self._path


class Package(object):
    ''' represent a parabola package '''

    def __init__(self, package, database):
        ''' constructor '''
        self._fullname = package
        self._database = database

        match = re.match(r'^(.*)-([^-]*-[^-]*)-([^-]*)$', package)
        if match is None:
            raise ValueError('package %s is not valid' % package)
        self._pkgname = match.group(1)
        self._versions = [Version(match.group(2)), None, None]
        self._arch = match.group(3)

        self._chroot = Chroot(
            CONFIG.parabola.native_arch if self._arch == 'any' else self._arch,
            self._database
        )
        self._chroot.update()

    @property
    def pkgname(self):
        ''' produce the name of the package '''
        return self._pkgname

    @property
    def arch(self):
        ''' produce the arch of the package '''
        return self._arch

    @property
    def database(self):
        ''' produce the database of the package '''
        return self._database

    @property
    def target_version(self):
        ''' produce the version of the package currently in the PKGBUILD '''
        return self._versions[0]

    @property
    def actual_version(self):
        ''' produce the version of the package currently in the database '''
        if self._versions[1] is None:
            self._versions[1] = self._chroot.get_version_of(
                '%s/%s' % (self._database, self._pkgname)
            )
            logging.info('%s-%s: actual version is %s', self._pkgname,
                         self._arch, self._versions[1])
        return self._versions[1]

    @property
    def latest_version(self):
        ''' produce the latest version available of the package from upstream '''
        if self._versions[2] is None:
            self._versions[2] = VersionMaster.get_latest_version(self)
            logging.info('%s-%s: latest version is %s', self._pkgname,
                         self._arch, self._versions[2])
        return self._versions[2]

    def can_install(self):
        ''' determine whether the package can be installed '''
        return self._chroot.can_install(self)

    def __lt__(self, other):
        ''' comparison operator for sorting '''
        return repr(self) < repr(other)

    def __repr__(self):
        ''' produce a string representation '''
        return self._fullname


class Version(object):
    ''' represent a package version '''

    def __init__(self, version, foreign=False):
        ''' constructor '''
        logging.info('constructing version from `%s`', version)
        self._full_version = version
        self._foreign = foreign

        self._pkgver = version
        self._pkgrel = None
        self._epoch = None

        if not foreign:
            self._pkgver, self._pkgrel = version.split('-')
        if not foreign and ':' in self._pkgver:
            self._epoch, self._pkgver = self._pkgver.split(':')

        self._epoch = parse_version(self._epoch) if self._epoch is not None else None
        self._pkgver = parse_version(self._pkgver)
        self._pkgrel = parse_version(self._pkgrel) if self._pkgrel is not None else None

    @property
    def foreign(self):
        ''' tell if the version is foreign '''
        return self._foreign

    @property
    def epoch(self):
        ''' produce the package epoch '''
        return self._epoch

    @property
    def pkgver(self):
        ''' produce the package pkgver '''
        return self._pkgver

    @property
    def pkgrel(self):
        ''' produce the package pkgrel '''
        return self._pkgrel

    def __eq__(self, other):
        ''' equals operator '''
        if self.foreign or other.foreign:
            return self.pkgver == other.pkgver

        return (self.epoch == other.epoch
                and self.pkgver == other.pkgver
                and self.pkgrel == other.pkgrel)

    def __gt__(self, other):
        ''' greater than operator '''
        if self.foreign or other.foreign:
            return self.pkgver > other.pkgver

        if self.epoch != other.epoch:
            return (other.epoch is None or other.epoch is not None
                    and self.epoch > other.epoch)
        if self.pkgver != other.pkgver:
            return self.pkgver > other.pkgver
        return self.pkgrel > other.pkgrel

    def __lt__(self, other):
        ''' less than operator '''
        if self.foreign or other.foreign:
            return self.pkgver < other.pkgver

        if self.epoch != other.epoch:
            return (self.epoch is None or other.epoch is not None
                    and self.epoch < other.epoch)
        if self.pkgver != other.pkgver:
            return self.pkgver < other.pkgver
        return self.pkgrel < other.pkgrel

    def __repr__(self):
        ''' produce a string representation '''
        return self._full_version


class VersionMaster(object):
    ''' manage fetching version numbers from upstream '''

    _fetch = {}
    _cache = {}

    @classmethod
    def get_latest_version(cls, package):
        ''' try and fetch the latest version for a given package '''
        if OFFLINE:
            return None

        match = next((key for key in cls._fetch if re.match(key, package.pkgname)), None)
        if match is None:
            return None

        fetch = cls._fetch[match]
        if fetch in cls._cache:
            return cls._cache[fetch]

        value = Version(fetch(), True)
        cls._cache[fetch] = value
        return value

    @classmethod
    def register(cls, regex):
        ''' register a version callback '''
        def wrap(func):
            ''' the wrapper, yo '''
            cls._fetch[r'^%s$' % regex] = func
            logging.info('registered version callback for %s', regex)
            return func
        return wrap

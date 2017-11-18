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


class Chroot(object):
    ''' represent a parabola build chroot '''

    cache = []

    def __init__(self, arch, database):
        ''' constructor '''
        self._arch = arch
        self._database = database
        self._name = '%s-%s' % (database, arch)

        self._pacman_conf = os.path.join(
            CONFIG.parabola.pacman_conf_path,
            'pacman.conf.%s.%s' % (database, arch)
        )
        if not os.path.exists(self._pacman_conf):
            self._pacman_conf = os.path.join(
                CONFIG.parabola.pacman_conf_path,
                'pacman.conf.%s' % arch
            )

        tmp = sh.sudo.librechroot.bake(
            A=self._arch,
            C=self._pacman_conf,
            n=self._name,
            _err=_LOG
        )
        self._librechroot = tmp.bake(_out=_LOG)
        self._pacman = tmp.run.pacman.bake()

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
        if self.name in self.cache:
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


class Repo(object):
    ''' represent the parabola package repository '''

    def __init__(self, path):
        ''' constructor '''
        self._path = path
        self._git = sh.git.bake(
            _cwd=path,
            _out=_LOG,
            _err=_LOG
        )
        self._grep = sh.grep.bake(
            '-lR',
            _cwd=path,
            _err=_LOG
        )

    def update(self):
        ''' update the repo '''
        self._git.pull()

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

        self._makepkg = sh.makepkg.bake(
            _cwd=os.path.dirname(path),
            _err=_LOG
        )

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
            self._chroot.update()
            self._versions[1] = self._chroot.get_version_of(
                '%s/%s' % (self._database, self._pkgname)
            )
        return self._versions[1]

    @property
    def latest_version(self):
        ''' produce the latest version available of the package from upstream '''
        if self._versions[2] is None:
            self._versions[2] = VersionMaster.get_latest_version(self)
        return self._versions[2]

    def __lt__(self, other):
        ''' comparison operator for sorting '''
        return repr(self) < repr(other)

    def __repr__(self):
        ''' produce a string representation '''
        return self._fullname


class Version(object):
    ''' represent a package version '''

    def __init__(self, version):
        ''' constructor '''
        self._full_version = version

        self._pkgver = version
        self._pkgrel = None
        if '-' in version:
            self._pkgver, self._pkgrel = version.split('-')
        self._epoch = None
        if ':' in self._pkgver:
            self._epoch, self._pkgver = self._pkgver.split(':')

        self._epoch = parse_version(self._epoch) if self._epoch is not None else None
        self._pkgver = parse_version(self._pkgver)
        self._pkgrel = parse_version(self._pkgrel) if self._pkgrel is not None else None

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
        return (self.epoch == other.epoch
                and self.pkgver == other.pkgver
                and self.pkgrel == other.pkgrel)

    def __gt__(self, other):
        ''' greater than operator '''
        if self.epoch != other.epoch:
            return other.epoch is None or self.epoch > other.epoch
        if self.pkgver != other.pkgver:
            return self.pkgver > other.pkgver
        return other.pkgrel is None or self.pkgrel > other.pkgrel

    def __lt__(self, other):
        ''' less than operator '''
        if self.epoch != other.epoch:
            return self.epoch is None or self.epoch < other.epoch
        if self.pkgver != other.pkgver:
            return self.pkgver < other.pkgver
        return self.pkgrel is None or self.pkgrel < other.pkgrel

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
        if package.pkgname not in cls._fetch:
            return None

        if package.pkgname not in cls._cache:
            value = cls._fetch[package.pkgname]()
            value = Version(value) if value is not None else None
            for pkg in cls._fetch[package.pkgname].group:
                cls._cache[pkg] = value
        return cls._cache[package.pkgname]

    @classmethod
    def register(cls, name):
        ''' register a version callback '''
        def wrap(func):
            ''' the wrapper, yo '''
            try:
                func.group.append(name)
            except AttributeError:
                func.group = [name]
            cls._fetch[name] = func
            logging.info('registered version callback for %s %s', name, func.group)
            return func
        return wrap

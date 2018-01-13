'''
parabola repo functions
'''

import logging
import re
import os
import sh
import xdg


class Package(object):
    ''' represent a parabola Package '''

    def __init__(self, pkgbuild, name, version):
        ''' constructor '''
        self._pkgbuild = pkgbuild
        self._name = name
        self._version = version
        logging.debug('creating package for %s-%s', name, version)

        self._arches = []

    def add_arch(self, arch):
        ''' add a built arch to the package '''
        self._arches.append(arch)

    @property
    def name(self):
        ''' produce the name of the package '''
        return self._name

    @property
    def longname(self):
        ''' produce the long name of the package, consisting of name and version '''
        return '%s/%s' % (self._pkgbuild.repodb.name, self._name)

    @property
    def arches(self):
        ''' produce the list of arches of the package '''
        return self._arches

    def __repr__(self):
        ''' produce a string representation '''
        return 'Package::%s/%s-%s' % (self._pkgbuild.repodb.name, self._name, self._version)


class Pkgbuild(object):
    ''' represent a parabola PKGBUILD '''

    def __init__(self, repodb, name):
        ''' constructor '''
        self._repodb = repodb
        self._name = name
        self._path = os.path.join(repodb.path, name)
        logging.debug('creating PKGBUILD "%s" at %s', name, self._path)

        self._packages = {}
        self._load_packages()

    def _load_packages(self):
        ''' load the packages from the PKGBUILD '''
        for line in self._packagelist().split():
            match = re.match(r'^(.*)-([^-]*-[^-]*)-([^-]*)$', line)

            name = match.group(1)
            version = match.group(2)
            arch = match.group(3)

            if name not in self._packages:
                self._packages[name] = Package(self, name, version)
            self._packages[name].add_arch(arch)

    def _packagelist(self):
        ''' get the packagelist from cache or from the PKGBUILD itself '''
        cache = os.path.join(xdg.XDG_CACHE_HOME, 'parabola-repolint',
                             self._repodb.name, self._name)

        if os.path.isfile(cache) and os.path.getmtime(cache) > os.path.getmtime(self._path):
            with open(cache) as cachefile:
                return cachefile.read()

        res = sh.makepkg('--packagelist', _cwd=self._path)
        os.makedirs(os.path.dirname(cache), exist_ok=True)

        with open(cache, 'w') as cachefile:
            cachefile.write(str(res))
        return res

    @property
    def repodb(self):
        ''' produce the repodb of the pkgbuild '''
        return self._repodb

    @property
    def name(self):
        ''' produce the name of the PKGBUILD '''
        return self._name

    @property
    def packages(self):
        ''' produce the list of packages in this pkgbuild '''
        return self._packages.values()

    def __repr__(self):
        ''' produce a string representation '''
        return 'PKGBUILD@%s' % self._path


class RepoDb(object):
    ''' represent a database in the parabola package repository '''

    def __init__(self, repo, name):
        ''' constructor '''
        self._repo = repo
        self._name = name
        self._path = os.path.join(repo.path, name)
        logging.debug('creating RepoDb "%s" at %s', name, self._path)

        self._pkgbuilds = {}
        self._package_index = {}

        self._load_packages()

    def _load_packages(self):
        ''' load all PKGBUILDs and packages from the repo and build an index '''
        logging.debug('loading pkgbuilds from %s', self)
        for name in os.listdir(self._path):
            try:
                self._pkgbuilds[name] = Pkgbuild(self, name)
            except sh.ErrorReturnCode:
                logging.exception('no valid PKGBUILD at %s/%s', self._path, name)

        for pkgbuild in self._pkgbuilds.values():
            for package in pkgbuild.packages:
                self._package_index[package.longname] = package

    @property
    def name(self):
        ''' produce the name of the repodb '''
        return self._name

    @property
    def path(self):
        ''' produce the path to the repodb '''
        return self._path

    @property
    def pkgbuilds(self):
        ''' produce the list of pkgbuilds in this repo '''
        return self._pkgbuilds.values()

    @property
    def packages(self):
        ''' produce the list of packages in this repo '''
        return self._package_index

    def __repr__(self):
        ''' produce a string representation '''
        return 'RepoDb@%s' % self._path


class Repo(object):
    ''' represent the parabola package repository '''

    def __init__(self, path):
        ''' constructor '''
        logging.debug('creating Repo at %s', path)
        self._path = path
        self._repodbs = {}
        self._package_index = {}

    def update(self):
        ''' update the repo '''
        sh.git.pull(_cwd=self._path)

    def build_package_index(self, repodbs):
        ''' load all needed PKGBUILDS and packages and build an index '''
        logging.debug('loading packages from %s', repodbs)
        for repodb in repodbs:
            self._repodbs[repodb] = RepoDb(self, repodb)

        for repodb in self._repodbs.values():
            for pkgbuild in repodb.pkgbuilds:
                for package in pkgbuild.packages:
                    self._package_index[package.longname] = package

    @property
    def path(self):
        ''' produce the path to the repo '''
        return self._path

    @property
    def packages(self):
        ''' produce the list of all packages in the repo '''
        return self._package_index

    def __getitem__(self, key):
        ''' return the requested repodb '''
        return self._repodbs.__getitem__(key)

    def __repr__(self):
        ''' produce a string representation '''
        return 'Repo@%s' % self._path


class Librechroot(object):
    ''' represent a librechroot '''

    def __init__(self, arch, repodb):
        ''' constructor '''
        self._arch = arch
        self._repodb = repodb

        conf = os.path.join(xdg.XDG_DATA_HOME, 'arthur', 'pacman.conf.%s.%s' % (arch, repodb))
        os.makedirs(os.path.dirname(conf), exist_ok=True)
        if not os.path.isfile(conf):
            sh.cp('/usr/share/pacman/defaults/pacman.conf.%s' % arch, conf)
            sh.sed('-i', 's/^Architecture.*/Architecture = %s/' % arch, conf)
            sh.sed('-i', '/#\\[%s\\]/{s/^#//;n;s/^#//}' % repodb, conf)

        self._librechroot = sh.sudo.librechroot.bake(
            A=arch,
            C=conf,
            n='arthur-%s-%s' % (arch, repodb)
        )

    def update(self):
        ''' attempt to update the chroot '''
        self._librechroot.update()

    @property
    def run(self):
        ''' run something in the chroot '''
        return self._librechroot.run

    @property
    def arch(self):
        ''' proudce the arch of the chroot '''
        return self._arch

    @property
    def repodb(self):
        ''' produce the target repodb of the chroot '''
        return self._repodb
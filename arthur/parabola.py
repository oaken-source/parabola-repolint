'''
parabola repo functions
'''

import logging
import re
import os
import sh


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
        return '%s-%s' % (self._name, self._version)

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

    def load_packages(self):
        ''' load the packages from the PKGBUILD '''
        for line in sh.makepkg('--packagelist', _cwd=self._path).split():
            match = re.match(r'^(.*)-([^-]*-[^-]*)-([^-]*)$', line)

            name = match.group(1)
            version = match.group(2)
            arch = match.group(3)

            if name not in self._packages:
                self._packages[name] = Package(self, name, version)
            self._packages[name].add_arch(arch)

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
        logging.debug('creating RepoDb "%s" at %s', self._name, self._path)

        self._pkgbuilds = {}
        self._package_index = {}

    def load_pkgbuilds(self):
        ''' load all PKGBUILDs from the repo '''
        logging.debug('loading pkgbuilds from %s', self)
        for name in os.listdir(self._path):
            try:
                self._pkgbuilds[name] = Pkgbuild(self, name)
            except sh.ErrorReturnCode:
                logging.exception('no valid PKGBUILD at %s/%s', self._path, name)

    def load_packages(self):
        ''' load all packages from PKGBUILDs in the repo '''
        for pkgbuild in self._pkgbuilds.values():
            try:
                pkgbuild.load_packages()
            except sh.ErrorReturnCode:
                logging.exception('invalid pkgbuild at %s', pkgbuild)

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
        return self._package_index.values()

    def __repr__(self):
        ''' produce a string representation '''
        return 'RepoDb@%s' % self._path


class Repo(object):
    ''' represent the parabola package repository '''

    def __init__(self, path):
        ''' constructor '''
        self._path = path
        logging.debug('creating Repo at %s', self._path)

        self._repodbs = {}
        self._package_index = {}

        try:
            sh.git.pull(_cwd=path)
        except sh.ErrorReturnCode:
            logging.exception('failed to update repository at %s', path)

    def load_pkgbuilds(self, repodbs):
        ''' load all PKGBUILDs from the selected repos '''
        logging.debug('loading pkgbuilds from %s', repodbs)
        for repodb in repodbs:
            self._repodbs[repodb] = RepoDb(self, repodb)
            self._repodbs[repodb].load_pkgbuilds()

    def load_packages(self):
        ''' build an index of all packages '''
        logging.debug('loading all packages from %s', self._repodbs.values())
        for repodb in self._repodbs.values():
            repodb.load_packages()

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
        return self._package_index.values()

    def __getitem__(self, key):
        ''' return the requested repodb '''
        return self._repodbs.__getitem__(key)

    def __repr__(self):
        ''' produce a string representation '''
        return 'Repo@%s' % self._path

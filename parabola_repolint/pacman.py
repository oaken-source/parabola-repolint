'''
helpers for queries to pacman caches
'''

import os
import sh
import xdg
from pkg_resources import parse_version
from .config import CONFIG


class PacmanCache(object):
    ''' a pacman cache for arch or parabola '''

    def __init__(self, arch, repodb):
        ''' constructor '''
        self._arch = arch
        self._repodb = repodb

        self._cache_dir = os.path.join(xdg.XDG_CACHE_HOME, 'parabola-repolint',
                                       'pacman', arch, repodb)
        os.makedirs(self._cache_dir, exist_ok=True)

        if repodb in CONFIG.parabola.repodbs:
            mirror = CONFIG.mirrors.parabola
        elif arch == 'x86_64':
            mirror = CONFIG.mirrors.archlinux
        elif arch == 'i686':
            mirror = CONFIG.mirrors.archlinux32
        elif arch == 'armv7h':
            mirror = CONFIG.mirrors.archlinuxarm
        else:
            raise ValueError('no archlinux mirror for arch %s' % arch)

        self._mirrorlist = os.path.join(self._cache_dir, 'mirrorlist')
        with open(self._mirrorlist, 'w') as file:
            file.write('''
Server = %s
''' % mirror)

        self._pacman_conf = os.path.join(self._cache_dir, 'pacman.conf')
        with open(self._pacman_conf, 'w') as file:
            file.write('''
[options]
Architecture = %s
[%s]
Include = %s
''' % (arch, repodb, self._mirrorlist))

        self._pacman = sh.sudo.pacman.bake('--dbpath', self._cache_dir,
                                           '--config', self._pacman_conf)

        self._packages = {}

    def update(self):
        ''' update the pacman cache '''
        self._pacman('-Sy')

    def load_packages(self):
        ''' load the list of packages from the repo '''
        for line in self._pacman('-Sl', self._repodb).strip().split('\n'):
            _, pkgname, version = line.split(' ')
            self._packages[pkgname] = (pkgname, parse_version(version.split('-')[0]))

    @property
    def packages(self):
        ''' produce the list of packages in the pacman cache '''
        return self._packages

    def __repr__(self):
        ''' produce a string representation '''
        return 'PacmanCache@%s-%s' % (self._repodb, self._arch)

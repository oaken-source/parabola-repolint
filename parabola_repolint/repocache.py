'''
repo cache management classes
'''

import os
import shutil
import logging

import sh
from xdg import BaseDirectory

from parabola_repolint.config import CONFIG


class Package():
    ''' represent a parabola package '''

    def __init__(self, repo, path):
        ''' constructor '''
        self._repo = repo
        self._path = path

        self._repo = repo
        self._arch = os.path.basename(os.path.dirname(path))

        mtime = os.path.getmtime(self._path)
        cache_path = path + '.pkginfo'

        self._data = {}
        data = self._cached_pacinfo(cache_path, mtime)
        cur = None
        for line in data.splitlines():
            if not line:
                continue
            if line[16] == ':':
                cur, line = line.split(':', 1)
                cur = cur.strip()
            line = line.strip()
            if cur in self._data:
                self._data[cur] += ' ' + line
            else:
                self._data[cur] = line

        self._pkgbuild = repo.find_pkgbuild(self.pkgname)
        if self._pkgbuild is None and self.pkgname.endswith('-debug'):
            self._pkgbuild = repo.find_pkgbuild(self.pkgname[:-6])

    def _cached_pacinfo(self, cachefile, mtime):
        ''' get information from a package '''
        if os.path.isfile(cachefile) and os.path.getmtime(cachefile) > mtime:
            with open(cachefile, 'r') as infile:
                return infile.read()

        res = ''
        try:
            res = str(sh.pacman('-Qip', self._path))
        except sh.ErrorReturnCode:
            logging.exception('pacman -Qip failed for %s', self)

        with open(cachefile, 'w') as outfile:
            outfile.write(res)

        return res

    @property
    def path(self):
        ''' produce the path to the package file '''
        return self._path

    @property
    def pkgbuild(self):
        ''' produce the pkgbuild to the package '''
        return self._pkgbuild

    @property
    def pkgname(self):
        ''' produce the name of the package '''
        return self._data['Name']

    def __repr__(self):
        ''' produce a string representation '''
        return "%s/%s/%s" % (self._repo, self._arch, os.path.basename(self._path))


SRCINFO_VALUE = [
    'pkgbase',
    'pkgname',
    'pkgdesc',
    'pkgver',
    'pkgrel',
    'url',
    'epoch',
    'changelog',
]
SRCINFO_SET = [
    'arch',
    'license',
    'checkdepends',
    'conflicts',
    'depends',
    'provides',
    'groups',
    'install',
    'noextract',
    'backup',
    'makedepends',
    'optdepends',
    'replaces',
    'validpgpkeys',
]
SRCINFO_LIST = [
    'source',
    'md5sums',
    'sha1sums',
    'sha256sums',
    'sha512sums',
    'options',
]

for ARCH in CONFIG.parabola.arches:
    SRCINFO_SET.extend([
        'depends_%s' % ARCH,
        'makedepends_%s' % ARCH,
    ])
    SRCINFO_LIST.extend([
        'source_%s' % ARCH,
        'sha256sums_%s' % ARCH,
        'sha512sums_%s' % ARCH,
    ])


class Srcinfo():
    ''' represent the PKGBUILD srcinfo '''

    def __init__(self, srcinfo):
        ''' constructor '''
        self._srcinfo_str = srcinfo

        self._pkgbase = {}
        self._pkginfo = {}

        current_dict = self._pkgbase

        for line in srcinfo.splitlines():
            line = line.strip()
            if not line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if key == 'pkgname':
                self._pkginfo[value] = {}
                current_dict = self._pkginfo[value]

            if key in SRCINFO_VALUE:
                current_dict[key] = value
            elif key in SRCINFO_SET:
                if key not in current_dict:
                    current_dict[key] = set()
                current_dict[key].add(value)
            elif key in SRCINFO_LIST:
                if key not in current_dict:
                    current_dict[key] = list()
                current_dict[key].append(value)
            else:
                logging.warning('unhandled SRCINFO key: %s', key)

    @property
    def pkgbase(self):
        ''' the pkgbase information '''
        return self._pkgbase

    @property
    def pkginfo(self):
        ''' the information of split packages '''
        return self._pkginfo


class Pkgbuild():
    ''' represent a PGKBUILD file '''

    def __init__(self, repo, path):
        ''' constructor '''
        self._repo = repo
        self._path = os.path.dirname(path)

        self._valid = None
        self._srcinfo = None
        self._pkglist = None

    @property
    def valid(self):
        ''' indicate whether the PKGBUILD file is valid '''
        if self._valid is None:
            self._load_metadata()
        return self._valid

    @property
    def pkglist(self):
        ''' produce the list of packages in the PKGBUILD '''
        if self._valid is None:
            self._load_metadata()
        return self._pkglist

    @property
    def srcinfo(self):
        ''' produce the srcinfo of the PKGBUILD '''
        if self._valid is None:
            self._load_metadata()
        return self._srcinfo

    def _load_metadata(self):
        ''' attempt to parse the PKGBUILD '''
        mtime = os.path.getmtime(os.path.join(self._path, 'PKGBUILD'))

        srcinfo = os.path.join(self._path, '.srcinfo')
        srcinfo_str = self._cached_makepkg(srcinfo, mtime, '--printsrcinfo')

        pkglist = os.path.join(self._path, '.pkglist')
        pkglist_str = self._cached_makepkg(pkglist, mtime, '--packagelist')

        self._valid = srcinfo_str and pkglist_str
        if self._valid:
            self._srcinfo = Srcinfo(srcinfo_str)
            self._pkglist = pkglist_str.split()

    def _cached_makepkg(self, cachefile, mtime, *args, **kwargs):
        ''' speed up makepkg calls by caching results '''
        if os.path.isfile(cachefile) and os.path.getmtime(cachefile) > mtime:
            with open(cachefile, 'r') as infile:
                return infile.read()

        res = ''
        try:
            res = str(sh.makepkg(*args, **kwargs, _cwd=self._path))
        except sh.ErrorReturnCode:
            logging.exception('makepkg failed for %s', self)

        with open(cachefile, 'w') as outfile:
            outfile.write(res)

        return res

    def _set_srcinfo(self, srcinfo):
        ''' parse the pkgubilds srcinfo '''
        self._srcinfo = srcinfo

    def _set_pkglist(self, pkglist):
        ''' parse the pkgbuilds pkglist '''
        self._pkglist = pkglist.split()

    def __repr__(self):
        ''' a string representation '''
        return 'PKGBUILD @ %s' % self._path


class Repo():
    ''' represent a single pacman repository '''

    def __init__(self, name, pkgbuild_dir, package_dir):
        ''' constructor '''
        self._name = name
        self._pkgbuild_dir = pkgbuild_dir
        self._package_dir = package_dir

        self._pkgbuilds = []
        for root, _, files in os.walk(self._pkgbuild_dir):
            if 'PKGBUILD' in files:
                pkgbuild_path = os.path.join(root, 'PKGBUILD')
                self._pkgbuilds.append(Pkgbuild(self, pkgbuild_path))

        self._packages = []
        for root, _, files in os.walk(self._package_dir):
            for pkg in [f for f in files if f.endswith('.pkg.tar.xz')]:
                package_path = os.path.join(root, pkg)
                self._packages.append(Package(self, package_path))

    @property
    def pkgbuilds(self):
        ''' produce the list of pkgbuilds in the repo '''
        return self._pkgbuilds

    @property
    def packages(self):
        ''' produce the list of packages in the repo '''
        return self._packages

    def find_pkgbuild(self, pkgname):
        ''' find a pkgbuild by pkgname '''
        for pkgbuild in self.pkgbuilds:
            if pkgname in pkgbuild.srcinfo.pkginfo:
                return pkgbuild

    def __repr__(self):
        ''' produce a string representation of the repo '''
        return '[%s]' % self._name


class RepoCache():
    ''' the cache manager '''

    def __init__(self):
        ''' constructor '''
        self._giturl = CONFIG.parabola.abslibre

        self._cache_dir = os.path.join(BaseDirectory.xdg_cache_home, 'parabola-repolint')
        self._abslibre_dir = os.path.join(self._cache_dir, 'abslibre')
        self._packages_dir = os.path.join(self._cache_dir, 'packages')

        self._repo_names = CONFIG.parabola.repos
        self._arches = CONFIG.parabola.arches

        self._repos = []

    @property
    def pkgbuilds(self):
        ''' produce the list of pkgbuilds in all repos '''
        return [p for r in self._repos for p in r.pkgbuilds]

    @property
    def packages(self):
        ''' produce the list of packages in all repos '''
        return [p for r in self._repos for p in r.packages]

    def load_repos(self, noupdate, ignore_cache):
        ''' update and load repo data from cache '''
        os.makedirs(self._cache_dir, exist_ok=True)

        if ignore_cache:
            shutil.rmtree(self._cache_dir)
            os.makedirs(self._cache_dir, exist_ok=True)

        if not noupdate:
            self._update_abslibre()
            self._update_packages()

        for repo in self._repo_names:
            pkgbuild_dir = os.path.join(self._abslibre_dir, repo)
            packages_dir = os.path.join(self._packages_dir, repo)
            self._repos.append(Repo(repo, pkgbuild_dir, packages_dir))

    def _update_abslibre(self):
        ''' update the PKGBUILDs '''
        if not os.path.exists(self._abslibre_dir):
            sh.git.clone(self._giturl, 'abslibre', _cwd=self._cache_dir)
        sh.git.pull(_cwd=self._abslibre_dir)

    def _update_packages(self):
        ''' update the package cache '''
        for repo in self._repo_names:
            for arch in self._arches:
                for mirror in CONFIG.mirrors:
                    if arch in mirror.arches and repo in mirror.repos:
                        self._update_from_mirror(repo, arch, mirror.mirror)

    def _update_from_mirror(self, repo, arch, mirror):
        ''' update the package cache from a given mirror '''
        remote = mirror % dict(repo=repo, arch=arch)
        local = os.path.join(self._packages_dir, repo)
        os.makedirs(local, exist_ok=True)
        sh.rsync('-a', '-L', '--delete-after', '--filter', 'P *.pkginfo', remote, local)

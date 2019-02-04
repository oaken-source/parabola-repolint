'''
repo cache management classes
'''

import os
import shutil
import logging

import sh
from xdg import BaseDirectory

from parabola_repolint.config import CONFIG


class PkgFile():
    ''' represent a parabola pkg.tar.xz file '''

    def __init__(self, repo, path):
        ''' constructor '''
        self._repo = repo
        self._path = path

        self._repoarch = os.path.basename(os.path.dirname(path))

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

        self._pkgbuilds = repo.pkgbuild_cache.get(self.pkgname, [])
        if not self._pkgbuilds and self.pkgname.endswith('-debug'):
            self._pkgbuilds = repo.pkgbuild_cache.get(self.pkgname[:-6], [])
        for pkgbuild in self._pkgbuilds:
            pkgbuild.register_pkgfile(self)

        self._pkgentries = repo.pkgentries_cache[self._repoarch].get(self.pkgname, [])
        if not self._pkgentries and self.pkgname.endswith('-debug'):
            self._pkgentries = repo.pkgentries_cache[self._repoarch].get(self.pkgname[:-6], [])
        for pkgentry in self._pkgentries:
            pkgentry.register_pkgfile(self)
        print(self._pkgentries)

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
    def pkgbuilds(self):
        ''' produce the pkgbuilds to the package '''
        return self._pkgbuilds

    @property
    def pkgentries(self):
        ''' produce the pkgentries to the pkgfile '''
        return self._pkgentries

    @property
    def repo(self):
        ''' produce the repo of the package '''
        return self._repo

    @property
    def pkgname(self):
        ''' produce the name of the package '''
        return self._data['Name']

    @property
    def arch(self):
        ''' produce the architecture of the package '''
        return self._repoarch

    def __repr__(self):
        ''' produce a string representation '''
        path = self._path
        path, pkgfile = os.path.split(path)
        path, arch = os.path.split(path)
        _, repo = os.path.split(path)
        return "%s/%s/%s" % (repo, arch, pkgfile)


class PkgEntry():
    ''' represent an entry in a repo.db '''

    def __init__(self, repo, path):
        ''' constructor '''
        self._repo = repo
        self._path = path

        self._repoarch = os.path.basename(os.path.dirname(path))

        with open(os.path.join(path, 'desc'), 'r') as infile:
            data = infile.read()

        self._data = {}
        cur = None
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            if line[0] == '%' and line[-1] == '%':
                cur = line[1:-1]
                continue
            if cur in self._data:
                self._data[cur] += ' ' + line
            else:
                self._data[cur] = line

        self._pkgbuilds = repo.pkgbuild_cache.get(self.pkgname, [])
        if not self._pkgbuilds and self.pkgname.endswith('-debug'):
            self._pkgbuilds = repo.pkgbuild_cache.get(self.pkgname[:-6], [])
        for pkgbuild in self._pkgbuilds:
            pkgbuild.register_pkgentry(self)

        self._pkgfiles = []

    def register_pkgfile(self, pkgfile):
        ''' add a pkgfile to this pkgentry '''
        self._pkgfiles.append(pkgfile)

    @property
    def pkgname(self):
        ''' produce the name of the package '''
        return self._data['NAME']

    @property
    def arch(self):
        ''' produce the architecture of the package '''
        return self._repoarch

    @property
    def pkgbuilds(self):
        ''' produce the pkgbuilds associated with the pkgentry '''
        return self._pkgbuilds

    @property
    def pkgfiles(self):
        ''' produce the pkgfiles associated with this pkgentry '''
        return self._pkgfiles

    def __repr__(self):
        ''' produce a string representation '''
        path = self._path
        path, _ = os.path.split(path)
        path, arch = os.path.split(path)
        _, repo = os.path.split(path)
        return "%s/%s/%s" % (repo, arch, self.pkgname)


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


class PkgBuild():
    ''' represent a PGKBUILD file '''

    def __init__(self, repo, path):
        ''' constructor '''
        self._repo = repo
        self._path = os.path.dirname(path)

        self._valid = None
        self._srcinfo = None
        self._pkglist = None

        self._pkgentries = []
        self._pkgfiles = []

    def register_pkgentry(self, pkgentry):
        ''' add a pkgentry to this pkgbuild '''
        self._pkgentries.append(pkgentry)

    def register_pkgfile(self, pkgfile):
        ''' add a pkgfile to this pkgbuild '''
        self._pkgfiles.append(pkgfile)

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

    @property
    def pkgentries(self):
        ''' produce the list of pkgentries linked to this pkgbuild '''
        return self._pkgentries

    @property
    def pkgfiles(self):
        ''' produce the list of pkgfiles linked to this pkgbuild '''
        return self._pkgfiles

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

    def __repr__(self):
        ''' a string representation '''
        return 'PKGBUILD @ %s' % self._path


class Repo():
    ''' represent a single pacman repository '''

    def __init__(self, name, pkgbuild_dir, pkgentries_dir, pkgfiles_dir):
        ''' constructor '''
        self._name = name
        self._arches = CONFIG.parabola.arches

        self._pkgbuild_dir = pkgbuild_dir
        self._pkgentries_dir = pkgentries_dir
        self._pkgfiles_dir = pkgfiles_dir

        self._pkgbuilds = []
        self._pkgbuild_cache = {}
        self._load_pkgbuilds()

        self._pkgentries = []
        self._pkgentries_cache = {}
        self._load_pkgentries()

        self._pkgfiles = []
        self._load_pkgfiles()

    @property
    def pkgbuilds(self):
        ''' produce the list of pkgbuilds in the repo '''
        return self._pkgbuilds

    @property
    def pkgbuild_cache(self):
        ''' produce the list of pkgbuilds by pkgname '''
        return self._pkgbuild_cache

    @property
    def pkgentries(self):
        ''' produce the list of packages in the repo.db '''
        return self._pkgentries

    @property
    def pkgentries_cache(self):
        ''' produce the list of pkgentries by pkgname '''
        return self._pkgentries_cache

    @property
    def pkgfiles(self):
        ''' produce the list of pkg.tar.xz files in the repo '''
        return self._pkgfiles

    def _load_pkgbuilds(self):
        ''' load the pkgbuilds from abslibre '''
        for root, _, files in os.walk(self._pkgbuild_dir):
            if 'PKGBUILD' in files:
                pkgbuild = PkgBuild(self, os.path.join(root, 'PKGBUILD'))
                self._pkgbuilds.append(pkgbuild)
                for pkgname in pkgbuild.srcinfo.pkginfo:
                    if pkgname not in self._pkgbuild_cache:
                        self._pkgbuild_cache[pkgname] = []
                    self._pkgbuild_cache[pkgname].append(pkgbuild)

    def _load_pkgentries(self):
        ''' extract and then load the entries in the db.tar.xz '''
        for arch in self._arches:
            src = os.path.join(self._pkgfiles_dir, arch)
            dst = os.path.join(self._pkgentries_dir, arch)

            os.makedirs(dst, exist_ok=True)
            shutil.rmtree(dst)
            os.makedirs(dst, exist_ok=True)

            sh.tar('xf', os.path.join(src, self._name + '.db'), _cwd=dst)

        for root, _, files in os.walk(self._pkgentries_dir):
            if 'desc' in files:
                pkgentry = PkgEntry(self, root)
                self._pkgentries.append(pkgentry)
                if pkgentry.arch not in self._pkgentries_cache:
                    self._pkgentries_cache[pkgentry.arch] = {}
                if pkgentry.pkgname not in self._pkgentries_cache[pkgentry.arch]:
                    self._pkgentries_cache[pkgentry.arch][pkgentry.pkgname] = []
                self._pkgentries_cache[pkgentry.arch][pkgentry.pkgname].append(pkgentry)

    def _load_pkgfiles(self):
        ''' load the pkg.tar.xz files from the repo '''
        for root, _, files in os.walk(self._pkgfiles_dir):
            for pkg in [f for f in files if f.endswith('.pkg.tar.xz')]:
                self._pkgfiles.append(PkgFile(self, os.path.join(root, pkg)))

    def __repr__(self):
        ''' produce a string representation of the repo '''
        return '[%s]' % self._name


class RepoCache():
    ''' the cache manager '''

    def __init__(self):
        ''' constructor '''
        self._cache_dir = os.path.join(BaseDirectory.xdg_cache_home, 'parabola-repolint')
        self._abslibre_dir = os.path.join(self._cache_dir, 'abslibre')
        self._pkgentries_dir = os.path.join(self._cache_dir, 'pkgentries')
        self._pkgfiles_dir = os.path.join(self._cache_dir, 'pkgfiles')

        self._repo_names = CONFIG.parabola.repos
        self._arches = CONFIG.parabola.arches

        self._repos = []

    @property
    def pkgbuilds(self):
        ''' produce the list of pkgbuilds in all repos '''
        return [p for r in self._repos for p in r.pkgbuilds]

    @property
    def pkgentries(self):
        ''' produce the list of packages in the repo.db's '''
        return [p for r in self._repos for p in r.pkgentries]

    @property
    def pkgfiles(self):
        ''' produce the list of pkg.tar.xz files in all repos '''
        return [p for r in self._repos for p in r.pkgfiles]

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
            pkgentries_dir = os.path.join(self._pkgentries_dir, repo)
            pkgfiles_dir = os.path.join(self._pkgfiles_dir, repo)
            self._repos.append(Repo(repo, pkgbuild_dir, pkgentries_dir, pkgfiles_dir))

    def _update_abslibre(self):
        ''' update the PKGBUILDs '''
        if not os.path.exists(self._abslibre_dir):
            giturl = CONFIG.parabola.abslibre
            sh.git.clone(giturl, 'abslibre', _cwd=self._cache_dir)
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
        local = os.path.join(self._pkgfiles_dir, repo)
        os.makedirs(local, exist_ok=True)
        sh.rsync('-a', '-L', '--delete-after', '--filter', 'P *.pkginfo', remote, local)

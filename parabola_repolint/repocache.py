'''
repo cache management classes
'''

import os
import shutil
import logging

import sh
from xdg import BaseDirectory

from parabola_repolint.config import CONFIG
from parabola_repolint.gnupg import GPG_PACMAN


BUILDINFO_VALUE = [
    'format',
    'pkgname',
    'pkgbase',
    'pkgver',
    'pkgarch',
    'pkgbuild_sha256sum',
    'packager',
    'builddate',
    'builddir',
]
BUILDINFO_SET = [
    'buildenv',
    'options',
]
BUILDINFO_LIST = [
    'installed',
]


class PkgFile():
    ''' represent a parabola pkg.tar.xz file '''

    def __init__(self, repo, path, repoarch):
        ''' constructor '''
        self._repo = repo
        self._path = path

        self._repoarch = repoarch

        mtime = os.path.getmtime(self._path)

        self._pkginfo = {}
        pkginfo = self._cached_pkginfo(path + '.pkginfo', mtime)
        cur = None
        for line in pkginfo.splitlines():
            if not line:
                continue
            if line[16] == ':':
                cur, line = line.split(':', 1)
                cur = cur.strip()
            line = line.strip()
            if cur in self._pkginfo:
                self._pkginfo[cur] += ' ' + line
            else:
                self._pkginfo[cur] = line

        self._buildinfo = {}
        # only parse .BUILDINFO for parabola packages
        if repo.name in CONFIG.parabola.repos:
            buildinfo = self._cached_buildinfo(path + '.buildinfo', mtime)
            for line in buildinfo.splitlines():
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                if key in BUILDINFO_VALUE:
                    self._buildinfo[key] = value
                elif key in BUILDINFO_SET:
                    if key not in self._buildinfo:
                        self._buildinfo[key] = set()
                    self._buildinfo[key].add(value)
                elif key in BUILDINFO_LIST:
                    if key not in self._buildinfo:
                        self._buildinfo[key] = list()
                    self._buildinfo[key].append(value)
                else:
                    logging.warning('unhandled BUILDINFO key: %s', key)

        pkgbuild_cache = repo.pkgbuild_cache.get(repoarch, {})
        self._pkgbuilds = pkgbuild_cache.get(self.pkgname, [])
        for pkgbuild in self._pkgbuilds:
            pkgbuild.register_pkgfile(self, repoarch)

        pkgentries_cache = repo.pkgentries_cache.get(repoarch, {})
        self._pkgentries = pkgentries_cache.get(self.pkgname, [])
        for pkgentry in self._pkgentries:
            pkgentry.register_pkgfile(self, repoarch)

    def _cached_pkginfo(self, cachefile, mtime):
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

    def _cached_buildinfo(self, cachefile, mtime):
        ''' get build information from a package '''
        if os.path.isfile(cachefile) and os.path.getmtime(cachefile) > mtime:
            with open(cachefile, 'r') as infile:
                return infile.read()

        res = ''
        try:
            res = str(sh.tar('-xOf', self._path, '.BUILDINFO'))
        except sh.ErrorReturnCode as ex:
            if b'.BUILDINFO: Not found in archive' not in ex.stderr:
                logging.exception('tar -xOf failed for %s', self)

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
        return self._pkginfo['Name']

    @property
    def arch(self):
        ''' produce the architecture of the package '''
        return self._repoarch

    def __repr__(self):
        ''' produce a string representation '''
        path = self._path
        path, pkgfile = os.path.split(path)
        path, arch = os.path.split(path)
        path, _ = os.path.split(path)
        _, repo = os.path.split(path)
        return "%s/%s/%s" % (repo, arch, pkgfile)


class PkgEntry():
    ''' represent an entry in a repo.db '''

    def __init__(self, repo, path, repoarch):
        ''' constructor '''
        self._repo = repo
        self._path = path

        self._repoarch = repoarch

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

        pkgbuild_cache = repo.pkgbuild_cache.get(repoarch, {})
        self._pkgbuilds = pkgbuild_cache.get(self.pkgname, [])
        for pkgbuild in self._pkgbuilds:
            pkgbuild.register_pkgentry(self, repoarch)

        self._pkgfiles = {}

    def register_pkgfile(self, pkgfile, arch):
        ''' add a pkgfile to this pkgentry '''
        if arch not in self._pkgfiles:
            self._pkgfiles[arch] = []
        self._pkgfiles[arch].append(pkgfile)

    @property
    def repo(self):
        ''' produce the repo of the package '''
        return self._repo

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
        path, _ = os.path.split(path)
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
        self._srcinfo = {}
        self._pkglist = {}
        self._arches = set()

        self._pkgentries = {}
        self._pkgfiles = {}

    def register_pkgentry(self, pkgentry, arch):
        ''' add a pkgentry to this pkgbuild '''
        if arch not in self._pkgentries:
            self._pkgentries[arch] = []
        self._pkgentries[arch].append(pkgentry)

    def register_pkgfile(self, pkgfile, arch):
        ''' add a pkgfile to this pkgbuild '''
        if arch not in self._pkgfiles:
            self._pkgfiles[arch] = []
        self._pkgfiles[arch].append(pkgfile)

    @property
    def repo(self):
        ''' produce the repo of the PKGBUILD '''
        return self._repo

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
    def arches(self):
        ''' produce the list of arches supported by this PKGBUILD '''
        if self._valid is None:
            self._load_metadata()
        return self._arches

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

        os.environ.pop('CARCH', None)
        si_file = os.path.join(self._path, '.srcinfo')
        si_str = self._cached_makepkg(si_file, mtime, '--printsrcinfo')

        if not si_str:
            self._valid = False
            return

        srcinfo = Srcinfo(si_str)

        self._arches = srcinfo.pkgbase['arch']
        if 'any' in self._arches:
            self._arches = self._arches.difference(['any'])
            self._arches = self._arches.union(CONFIG.parabola.arches)

        for arch in self._arches.intersection(CONFIG.parabola.arches):
            os.environ['CARCH'] = arch
            si_file = os.path.join(self._path, '.%s.srcinfo' % arch)
            si_str = self._cached_makepkg(si_file, mtime, '--printsrcinfo')
            pl_file = os.path.join(self._path, '.%s.pkglist' % arch)
            pl_str = self._cached_makepkg(pl_file, mtime, '--packagelist')
            os.environ.pop('CARCH', None)

            if not si_str or not pl_str:
                self._valid = False
                return

            self._srcinfo[arch] = Srcinfo(si_str)
            self._pkglist[arch] = pl_str.split()
            self._valid = True

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
        return '%s/%s/PKGBUILD' % (self._repo.name, os.path.basename(self._path))


class Repo():
    ''' represent a single pacman repository '''

    def __init__(self, name, pkgbuild_dir, pkgentries_dir, pkgfiles_dir):
        ''' constructor '''
        self._name = name

        self._pkgbuild_dir = pkgbuild_dir
        self._pkgentries_dir = pkgentries_dir
        self._pkgfiles_dir = pkgfiles_dir

        self._pkgbuilds = []
        self._pkgbuild_cache = {}
        if self._pkgbuild_dir is not None:
            self._load_pkgbuilds()
            logging.info('%s pkgbuilds: %s', name, self._pkgbuilds)
            logging.info('%s pkgbuild_cache: %s', name, self._pkgbuild_cache)

        self._pkgentries = []
        self._pkgentries_cache = {}
        self._load_pkgentries()

        logging.info('%s pkgentries: %s', name, self._pkgentries)
        logging.info('%s pkgentries_cache: %s', name, self._pkgentries_cache)

        self._pkgfiles = []
        self._load_pkgfiles()

        logging.info('%s pkgfiles: %s', name, self._pkgfiles)

    @property
    def name(self):
        ''' produce the name of the repo '''
        return self._name

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
                for arch in pkgbuild.arches.intersection(CONFIG.parabola.arches):
                    if arch not in self._pkgbuild_cache:
                        self._pkgbuild_cache[arch] = {}
                    pkgname = '%s-debug' % pkgbuild.srcinfo[arch].pkgbase['pkgbase']
                    if pkgname not in self._pkgbuild_cache[arch]:
                        self._pkgbuild_cache[arch][pkgname] = []
                    self._pkgbuild_cache[arch][pkgname].append(pkgbuild)
                    for pkgname in pkgbuild.srcinfo[arch].pkginfo:
                        if pkgname not in self._pkgbuild_cache[arch]:
                            self._pkgbuild_cache[arch][pkgname] = []
                        self._pkgbuild_cache[arch][pkgname].append(pkgbuild)

    def _load_pkgentries(self):
        ''' extract and then load the entries in the db.tar.xz '''
        for root, _, files in os.walk(self._pkgfiles_dir):
            if '%s.db' % self._name in files:
                arch = os.path.basename(root)
                if arch not in CONFIG.parabola.arches:
                    continue

                tar = os.path.join(root, self._name + '.db')
                mtime = os.path.getmtime(tar)

                dst = os.path.join(self._pkgentries_dir, 'os', arch)
                if os.path.isdir(dst) and os.path.getmtime(dst) > mtime:
                    continue

                os.makedirs(dst, exist_ok=True)
                shutil.rmtree(dst)
                os.makedirs(dst, exist_ok=True)

                sh.tar('xf', os.path.join(root, self._name + '.db'), _cwd=dst)

        for root, _, files in os.walk(self._pkgentries_dir):
            if 'desc' in files:
                arch = os.path.basename(os.path.dirname(root))
                if arch not in CONFIG.parabola.arches:
                    continue

                pkgentry = PkgEntry(self, root, arch)
                self._pkgentries.append(pkgentry)
                if pkgentry.arch not in self._pkgentries_cache:
                    self._pkgentries_cache[pkgentry.arch] = {}
                if pkgentry.pkgname not in self._pkgentries_cache[pkgentry.arch]:
                    self._pkgentries_cache[pkgentry.arch][pkgentry.pkgname] = []
                self._pkgentries_cache[pkgentry.arch][pkgentry.pkgname].append(pkgentry)

    def _load_pkgfiles(self):
        ''' load the pkg.tar.xz files from the repo '''
        for root, _, files in os.walk(self._pkgfiles_dir):
            arch = os.path.basename(root)
            if arch not in CONFIG.parabola.arches:
                continue

            for pkg in files:
                if pkg.endswith('.pkg.tar.xz'):
                    self._pkgfiles.append(PkgFile(self, os.path.join(root, pkg), arch))

    def __repr__(self):
        ''' produce a string representation of the repo '''
        return '[%s]' % self._name


ARCH_REPOS = {'core', 'extra', 'community'}


class RepoCache():
    ''' the cache manager '''

    def __init__(self):
        ''' constructor '''
        cache_base_dir = BaseDirectory.xdg_cache_home
        self._cache_dir = os.path.join(cache_base_dir, 'parabola-repolint')
        self._abslibre_dir = os.path.join(self._cache_dir, 'abslibre')
        self._pkgentries_dir = os.path.join(self._cache_dir, 'pkgentries')
        self._pkgfiles_dir = os.path.join(self._cache_dir, 'pkgfiles')
        self._keyring_dir = os.path.join(self._cache_dir, 'keyring')

        self._repo_names = CONFIG.parabola.repos
        self._arches = CONFIG.parabola.arches

        self._repos = {}
        self._arch_repos = {}
        self._keyring = []

    @property
    def pkgbuilds(self):
        ''' produce the list of pkgbuilds in all repos '''
        return [p for r in self._repos.values() for p in r.pkgbuilds]

    @property
    def pkgentries(self):
        ''' produce the list of packages in the repo.db's '''
        return [p for r in self._repos.values() for p in r.pkgentries]

    @property
    def pkgfiles(self):
        ''' produce the list of pkg.tar.xz files in all repos '''
        return [p for r in self._repos.values() for p in r.pkgfiles]

    @property
    def arch_repos(self):
        ''' produce repo objects for core, extra and community '''
        return self._arch_repos

    @property
    def keyring(self):
        ''' produce the entries in the parabola keyring '''
        return self._keyring

    def load_repos(self, noupdate, ignore_cache):
        ''' update and load repo data from cache '''
        os.makedirs(self._cache_dir, exist_ok=True)

        if ignore_cache:
            shutil.rmtree(self._cache_dir)
            os.makedirs(self._cache_dir, exist_ok=True)

        if not noupdate:
            self._update_abslibre()
            self._update_packages()

        for repo in ARCH_REPOS:
            pkgentries_dir = os.path.join(self._pkgentries_dir, repo)
            pkgfiles_dir = os.path.join(self._pkgfiles_dir, repo)
            repo = Repo(repo, None, pkgentries_dir, pkgfiles_dir)
            self._arch_repos[repo.name] = repo

        for repo in self._repo_names:
            pkgbuild_dir = os.path.join(self._abslibre_dir, repo)
            pkgentries_dir = os.path.join(self._pkgentries_dir, repo)
            pkgfiles_dir = os.path.join(self._pkgfiles_dir, repo)
            repo = Repo(repo, pkgbuild_dir, pkgentries_dir, pkgfiles_dir)
            self._repos[repo.name] = repo

        self._extract_keyring()
        logging.info('keyring: %s', self._keyring)

    def _update_abslibre(self):
        ''' update the PKGBUILDs '''
        if not os.path.exists(self._abslibre_dir):
            giturl = CONFIG.parabola.abslibre
            sh.git.clone(giturl, 'abslibre', _cwd=self._cache_dir)
        sh.git.pull(_cwd=self._abslibre_dir)

    def _update_packages(self):
        ''' update the package cache '''
        remote = CONFIG.parabola.mirror
        local = self._pkgfiles_dir
        os.makedirs(local, exist_ok=True)
        sh.rsync('-a', '--delete-after', '--filter', 'P *.*info', remote, local)

    def _extract_keyring(self):
        ''' extract the parabola keyring '''
        cache = next(iter(self._repos['libre'].pkgentries_cache.values()))
        keyring_pkgentries = cache['parabola-keyring']
        keyring_pkgentry = keyring_pkgentries[0]
        keyring_pkgfile = next(iter(keyring_pkgentry.pkgfiles.values()))[0]

        src = keyring_pkgfile.path
        dst = self._keyring_dir

        if not os.path.isdir(dst) or os.path.getmtime(dst) > os.path.getmtime(src):
            os.makedirs(dst, exist_ok=True)
            shutil.rmtree(dst)
            os.makedirs(dst, exist_ok=True)
            sh.tar('xf', src, _cwd=dst)

        keyring_file = os.path.join(
            dst, 'usr', 'share', 'pacman', 'keyrings', 'parabola.gpg'
        )
        self._keyring = GPG_PACMAN.scan_keys(keyring_file)

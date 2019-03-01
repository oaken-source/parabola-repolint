'''
these are linter checks for PKGBUILD / .pkg.tar.xz / repo.db entry integrity
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class PkgBuildMissingPkgEntries(LinterCheckBase):
    '''
  for the list of packages produced by the pkgbuild for the supported arches,
  check whether an entry in a repo.db exists for each of them. The check reports
  an issue whenever a repo.db entry is missing for a package that should be
  produced.
'''

    name = 'pkgbuild_missing_pkgentries'
    check_type = LinterCheckType.PKGBUILD

    header = 'PKGBUILDs with missing entries in repo.db'

    def check(self, pkgbuild):
        ''' run the check '''
        missing = []
        for arch, info in pkgbuild.srcinfo.items():
            for pkgname in info.pkginfo:
                if pkgname not in [p.pkgname for p in pkgbuild.pkgentries.get(arch, [])]:
                    missing.append('%s/%s' % (arch, pkgname))
        if missing:
            raise LinterIssue('%s (%s)', pkgbuild, ','.join(missing))


# pylint: disable=no-self-use
class PkgBuildDuplicatePkgEntries(LinterCheckBase):
    '''
  for the list of packages produced by the pkgbuild for the supported arches,
  check whether duplicate entries in a repo.db exists for each of them. The check
  reports an issue whenever more than one repo.db entry exists for a package that
  should produced by the PKGBUILD.
'''

    name = 'pkgbuild_duplicate_pkgentries'
    check_type = LinterCheckType.PKGBUILD

    header = 'PKGBUILDs with duplicate entries in repo.db'

    def check(self, pkgbuild):
        ''' run the check '''
        duplicate = []
        for arch, info in pkgbuild.srcinfo.items():
            for pkgname in info.pkginfo:
                pkgentries = pkgbuild.pkgentries.get(arch, [])
                pkgentries = [p for p in pkgentries if p.pkgname == pkgname]
                if len(pkgentries) > 1:
                    duplicate.append('%s/%s: %s' % (arch, pkgname, ','.join(pkgentries)))
        if duplicate:
            raise LinterIssue('%s (%s)', pkgbuild, ','.join(duplicate))


# pylint: disable=no-self-use
class PkgBuildMissingPkgFiles(LinterCheckBase):
    '''
  for the list of packages produced by the pkgbuild for the supported arches,
  check whether a package file exists for each of them. The check reports an
  issue whenever a package file is missing for a package that should be produced.
'''

    name = 'pkgbuild_missing_pkgfiles'
    check_type = LinterCheckType.PKGBUILD

    header = 'PKGBUILDs with missing built packages'

    def check(self, pkgbuild):
        ''' run the check '''
        missing = []
        for arch, info in pkgbuild.srcinfo.items():
            for pkgname in info.pkginfo:
                if pkgname not in [p.pkgname for p in pkgbuild.pkgfiles.get(arch, [])]:
                    missing.append('%s/%s' % (arch, pkgname))
        if missing:
            raise LinterIssue('%s (%s)', pkgbuild, ','.join(missing))


# pylint: disable=no-self-use
class PkgEntryMissingPkgbuild(LinterCheckBase):
    '''
  for the list of entries in a repo.db, check whether a valid PKGBUILD exists
  that creates the entry. The check reports an issue for each repo.db entry that
  has no producing PKGBUILD.
'''

    name = 'pkgentry_missing_pkgbuild'
    check_type = LinterCheckType.PKGENTRY

    header = 'repo.db entries with no valid PKGBUILD'

    def check(self, pkgentry):
        ''' run the check '''
        if not pkgentry.pkgbuilds:
            raise LinterIssue('%s', pkgentry)


# pylint: disable=no-self-use
class PkgEntryDuplicatePkgbuilds(LinterCheckBase):
    '''
  for the list of entries in a repo.db, check whether more than one valid
  PKGBUILD exists that creates the entry. The check reports an issue for each
  repo.db entry that has more than one producing PKGBUILD.
'''

    name = 'pkgentry_duplicate_pkgbuilds'
    check_type = LinterCheckType.PKGENTRY

    header = 'repo.db entries with duplicate PKGBUILDs'

    def check(self, pkgentry):
        ''' run the check '''
        if len(pkgentry.pkgbuilds) > 1:
            duplicates = []
            for pkgbuild in pkgentry.pkgbuilds:
                duplicates.append(str(pkgbuild))
            raise LinterIssue('%s (%s)', pkgentry, ','.join(duplicates))


# pylint: disable=no-self-use
class PkgEntryMissingPkgFile(LinterCheckBase):
    '''
  for the list of entries in a repo.db, check wether a built package exists that
  backs the entry. The check reports an issue for each repo.db entry that is not
  associatable with a valid built package.
'''

    name = 'pkgentry_missing_pkgfile'
    check_type = LinterCheckType.PKGENTRY

    header = 'repo.db entries with no valid built package'

    def check(self, pkgentry):
        ''' run the check '''
        if not pkgentry.pkgfile:
            raise LinterIssue('%s', pkgentry)


# pylint: disable=no-self-use
class PkgFileMissingPkgbuild(LinterCheckBase):
    '''
  for the list of built packages, check whether a valid PKGBUILD exists that
  creates the package. The check reports an issue for each built package that has
  no producing PKGBUILD.
'''

    name = 'pkgfile_missing_pkgbuild'
    check_type = LinterCheckType.PKGFILE

    header = 'built packages with no valid PKGBUILD'

    def check(self, pkgfile):
        ''' run the check '''
        if not pkgfile.pkgbuilds:
            raise LinterIssue('%s (built %s)', pkgfile, pkgfile.build_date)


# pylint: disable=no-self-use
class PkgFileDuplicatePkgbuilds(LinterCheckBase):
    '''
  for the list of built packages, check whether more than one valid PKGBUILD
  exists that creates the package. The check reports an issue for each built
  package that has more than one producing PKGBUILD.
'''

    name = 'pkgfile_duplicate_pkgbuilds'
    check_type = LinterCheckType.PKGFILE

    header = 'built packages with duplicate PKGBUILDs'

    def check(self, pkgfile):
        ''' run the check '''
        if len(pkgfile.pkgbuilds) > 1:
            duplicates = []
            for pkgbuild in pkgfile.pkgbuilds:
                duplicates.append(str(pkgbuild))
            raise LinterIssue('%s (%s)', pkgfile, ','.join(duplicates))


# pylint: disable=no-self-use
class PkgFileMissingPkgEntry(LinterCheckBase):
    '''
  for the list of built packages, check wether a repo.db entry exists that refers
  to the package. The check reports an issue for each built package that is not
  referred to by a repo.db entry.
'''

    name = 'pkgfile_missing_pkgentry'
    check_type = LinterCheckType.PKGFILE

    header = 'built packages without a referring repo.db entry'

    def check(self, pkgfile):
        ''' run the check '''
        if not pkgfile.pkgentries:
            raise LinterIssue('%s (built %s)', pkgfile, pkgfile.build_date)


# pylint: disable=no-self-use
class PkgFileDuplicatePkgEntries(LinterCheckBase):
    '''
  for the list of built packages, check that at most one repo.db entry exists
  that refers to the package. The check reports an issue for each built package
  that is referred to by multiple repo.db entries.
'''

    name = 'pkgfile_duplicate_pkgentries'
    check_type = LinterCheckType.PKGFILE

    header = 'built packages with duplicate referring repo.db entries'

    def check(self, pkgfile):
        ''' run the check '''
        if len(pkgfile.pkgentries) > 1:
            raise LinterIssue('%s (%s)', pkgfile, ','.join(pkgfile.pkgentries))

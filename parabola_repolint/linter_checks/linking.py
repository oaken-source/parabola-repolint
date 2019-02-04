'''
these are linter checks for PKGBUILD / .pkg.tar.xz / repo.db entry integrity
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class PkgFileMissingPkgbuild(LinterCheckBase):
    ''' check for a .pkg.tar.xz without a PKGBUILD '''

    name = 'pkgfile_missing_pkgbuild'
    check_type = LinterCheckType.PKGFILE

    def check(self, pkgfile):
        ''' check for pkgfiles with nonexistant pkgbuild '''
        if not pkgfile.pkgbuilds:
            raise LinterIssue(pkgfile)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'pkgfiles with no associated valid PKGBUILD:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result


# pylint: disable=no-self-use
class PkgFileMultiplePkgbuilds(LinterCheckBase):
    ''' check for a .pkg.tar.xz with more than one PKGBUILD '''

    name = 'pkgfile_multiple_pkgbuilds'
    check_type = LinterCheckType.PKGFILE

    def check(self, pkgfile):
        ''' check for pkgfiles with too many PKGBUILDs '''
        if len(pkgfile.pkgbuilds) > 1:
            raise LinterIssue(pkgfile, pkgfile.pkgbuilds)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'pkgfiles with multiple associated PKGBUILDs:'
        for issue in issues:
            result += '\n    %s: %s' % (issue[0], issue[1])
        return result


# pylint: disable=no-self-use
class PkgFileMissingPkgEntry(LinterCheckBase):
    ''' check for a pkg.tar.xz that is not in the repo.db '''

    name = 'pkgfile_missing_pkgentry'
    check_type = LinterCheckType.PKGFILE

    def check(self, pkgfile):
        ''' check if the .pkg.tar.xz is part of the repo '''
        if not pkgfile.pkgentries:
            raise LinterIssue(pkgfile)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'pkgfiles not listed in repo.db:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result


# pylint: disable=no-self-use
class PkgFileMultiplePkgEntries(LinterCheckBase):
    ''' check for a pkg.tar.xz that has more than one entry in the repo.db '''

    name = 'pkgfile_multiple_pkgentries'
    check_type = LinterCheckType.PKGFILE

    def check(self, pkgfile):
        ''' check if the .pkg.tar.xz is part of the repo '''
        if len(pkgfile.pkgentries) > 1:
            raise LinterIssue(pkgfile, pkgfile.pkgentries)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'pkgfiles with multiple associated pkgentries:'
        for issue in issues:
            result += '\n    %s (%s)' % (issue[0], issue[1])
        return result


# pylint: disable=no-self-use
class PkgEntryMissingPkgbuild(LinterCheckBase):
    ''' check for an entry in a repo.db without a PKGBUILD '''

    name = 'pkgentry_missing_pkgbuild'
    check_type = LinterCheckType.PKGENTRY

    def check(self, pkgentry):
        ''' check for pkgentries with nonexistant pkgbuild '''
        if not pkgentry.pkgbuilds:
            raise LinterIssue(pkgentry)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'pkgentries with no associated valid PKGBUILD:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result


# pylint: disable=no-self-use
class PkgEntryMultiplePkgbuilds(LinterCheckBase):
    ''' check for a repo.db entry with more than one PKGBUILD '''

    name = 'pkgentry_multiple_pkgbuilds'
    check_type = LinterCheckType.PKGENTRY

    def check(self, pkgentry):
        ''' check for pkgentries with too many PKGBUILDs '''
        if len(pkgentry.pkgbuilds) > 1:
            raise LinterIssue(pkgentry, pkgentry.pkgbuilds)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'pkgentries with multiple associated PKGBUILDs:'
        for issue in issues:
            result += '\n    %s: %s' % (issue[0], issue[1])
        return result


# pylint: disable=no-self-use
class PkgEntryMissingPkgFile(LinterCheckBase):
    ''' check for an entry in the repo.db that is missing its pkg.tar.xz '''

    name = 'pkgentry_missing_pkgfile'
    check_type = LinterCheckType.PKGENTRY

    def check(self, pkgentry):
        ''' check if the the repo entry has at least one .pkg.tar.xz '''
        if not pkgentry.pkgfiles:
            raise LinterIssue(pkgentry)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'entries in repo.db missing a .pkg.tar.xz:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result


# pylint: disable=no-self-use
class PkgBuildMissingPkgEntry(LinterCheckBase):
    ''' check for a pkgbuild with no PkgEntries '''

    name = 'pkgbuild_missing_pkgentry'
    check_type = LinterCheckType.PKGBUILD

    def check(self, pkgbuild):
        ''' check that the pkgbuild produced at least one pkgentry '''
        if not pkgbuild.pkgentries:
            raise LinterIssue(pkgbuild)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'PKGBUILDs with no entries in repo.db:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result


# pylint: disable=no-self-use
class PkgBuildMissingPkgFile(LinterCheckBase):
    ''' check for a pkgbuild with no .pkg.tar.xz '''

    name = 'pkgbuild_missing_pkgfile'
    check_type = LinterCheckType.PKGBUILD

    def check(self, pkgbuild):
        ''' check for pkgbuilds with nonexistant pkgfiles '''
        if not pkgbuild.pkgfiles:
            raise LinterIssue(pkgbuild)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'PKGBUILDs with no .pkg.tar.xz:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result

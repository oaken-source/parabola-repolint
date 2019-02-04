'''
these are linter checks for PKGBUILD / .pkg.tar.xz / repo.db entry integrity
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


KNOWN_ARCHES = CONFIG.parabola.arches


# pylint: disable=no-self-use
class InvalidPkgbuild(LinterCheckBase):
    ''' check for invalid (broken) PKGBUILD files '''

    name = 'invalid_pkgbuild'
    check_type = LinterCheckType.PKGBUILD

    def check(self, pkgbuild):
        ''' check for invalid PKGBULDs in abslibre '''
        if not pkgbuild.valid:
            raise LinterIssue(pkgbuild)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'broken PKGBUILDs:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result


# pylint: disable=no-self-use
class UnsupportedArches(LinterCheckBase):
    ''' check for unsupported arches in a PKGBUILD '''

    name = 'unsupported_arches'
    check_type = LinterCheckType.PKGBUILD

    def check(self, pkgbuild):
        ''' check for unsupported architectures in the arch array '''
        if not pkgbuild.valid:
            return

        unsup = []

        unsup_base = pkgbuild.srcinfo.pkgbase['arch'].difference(KNOWN_ARCHES, ['any'])
        if unsup_base:
            unsup.append(': '.join(['pkgbase', ', '.join(unsup_base)]))

        for pkgname, pkginfo in pkgbuild.srcinfo.pkginfo.items():
            if 'arch' not in pkginfo:
                continue
            unsup_pkg = pkginfo['arch'].difference(unsup_base, KNOWN_ARCHES, ['any'])
            if unsup_pkg:
                unsup.append(': '.join([pkgname, ', '.join(unsup_pkg)]))

        if unsup:
            raise LinterIssue(pkgbuild, unsup)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'PKGBUILDs with unsupported arches:'
        for issue in issues:
            result += '\n    %s (%s)' % (issue[0], '; '.join(issue[1]))
        return result

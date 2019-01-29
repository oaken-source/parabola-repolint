'''
this is a linter check for unsupported architectures
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


KNOWN_ARCHES = CONFIG.parabola.arches


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

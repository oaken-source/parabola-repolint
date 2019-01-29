'''
this is a linter check for invalid PKGBUILDs
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


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

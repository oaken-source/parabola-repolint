'''
this is a linter check for PKGBUILDs that are out of date
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class OutOfDate(LinterCheckBase):
    ''' check for a pkgbuild with an out of date version '''

    name = 'out_of_date'
    check_type = LinterCheckType.PKGBUILD

    def check(self, pkgbuild):
        ''' check for a package version mismatch '''
        pass

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'PKGBUILDs that are out of date:'
        for issue in issues:
            result += '\n    %s (%s)' % (issue[0], issue[1])
        return result

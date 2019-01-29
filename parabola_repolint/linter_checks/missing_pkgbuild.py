'''
this is a linter check for missing PKGBUILDs
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


class MissingPkgbuild(LinterCheckBase):
    ''' check for a package without a PKGBUILD '''

    name = 'missing_pkgbuild'
    check_type = LinterCheckType.PACKAGE

    def check(self, package):
        ''' check for packages with nonexistant pkgbuild '''
        pass

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages with no associated valid PKGBUILD:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result

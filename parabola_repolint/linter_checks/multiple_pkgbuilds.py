'''
this is a linter check for packages with too many PKGBUILDs
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


class MultiplePkgbuilds(LinterCheckBase):
    ''' check for a package without more than one PKGBUILD '''

    name = 'multiple_pkgbuilds'
    check_type = LinterCheckType.PACKAGE

    def check(self, package):
        ''' check for packages with too many PKGBUILDs '''
        if len(package.pkgbuilds) > 1:
            raise LinterIssue(package, package.pkgbuilds)

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages with multiple associated PKGBUILDs:'
        for issue in issues:
            result += '\n    %s: %s' % (issue[0], issue[1])
        return result

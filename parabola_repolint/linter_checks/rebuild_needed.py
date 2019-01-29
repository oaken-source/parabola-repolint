'''
this is a linter check for packages that need rebuilds
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


class RebuildNeeded(LinterCheckBase):
    ''' check for a package with versions different from the PKGBUILD version '''

    name = 'rebuild_needed'
    check_type = LinterCheckType.PACKAGE

    def check(self, package):
        ''' check for a package version mismatch '''
        pass

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages that need rebuilds:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result

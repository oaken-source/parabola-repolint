'''
this is a linter check for packages that need rebuilds
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class RebuildNeeded(LinterCheckBase):
    ''' check for a package with versions different from the PKGBUILD version '''

    name = 'rebuild_needed'
    check_type = LinterCheckType.PKGFILE

    def check(self, package):
        ''' check for a package version mismatch '''
        pass

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages that need rebuilds:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result

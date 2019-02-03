'''
this is a linter check for package files that are not in the repository
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


class PackageNotInRepo(LinterCheckBase):
    ''' check for a package that is not in the repo.db '''

    name = 'package_not_in_repo'
    check_type = LinterCheckType.PACKAGE

    def check(self, package):
        ''' check if the package is part of the repo '''
        pass

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages not listed in repo.db:'
        for issue in issues:
            result += '\n    %s' % issue[0]
        return result

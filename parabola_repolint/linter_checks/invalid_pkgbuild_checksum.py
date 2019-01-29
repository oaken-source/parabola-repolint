'''
this is a linter check for packages that were not generated from
the version of the PKGBUILD in abslibre
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


class InvalidPkgbuildChecksum(LinterCheckBase):
    ''' check for a package with invalid pkgbuild checksum '''

    name = 'invalid_pkgbuild_checksum'
    check_type = LinterCheckType.PACKAGE

    def check(self, pkgbuild):
        ''' check for a package with pkgbuild checksum mismatch '''
        pass

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages with invalid PKGBUILD checksums  that are out of date:'
        for issue in issues:
            result += '\n    %s (%s)' % (issue[0], issue[1])
        return result

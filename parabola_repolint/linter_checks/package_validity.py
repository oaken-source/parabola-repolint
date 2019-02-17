'''
these are linter checks for general .pkg.tar.xz validity
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class PkgFileMissingBuildinfo(LinterCheckBase):
    '''
  for the list of built packages in the repos, check wether each has an embedded
  .BUILDINFO file, containing information about the build environment and the
  PKGBUILD the package is built from. This check reports an issue whenever a
  built package is found that has no .BUILDINFO file.
'''

    name = 'pkgfile_missing_buildinfo'
    check_type = LinterCheckType.PKGFILE

    header = 'built packages with no .BUILDINFO file'

    def check(self, pkgfile):
        ''' run the check '''
        if not pkgfile.buildinfo:
            raise LinterIssue(pkgfile, pkgfile.build_date)

    def format(self, issues):
        ''' format the list of found issues '''
        result = []
        for issue in issues:
            result.append('    %s (built %s)' % (issue[0], issue[1]))
        return "\n".join(sorted(result))

'''
these are linter checks for general .pkg.tar.xz validity
'''

import hashlib

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class PkgFileMissingBuildinfo(LinterCheckBase):
    '''
  for the list of built packages in the repos, check whether each has an embedded
  .BUILDINFO file, containing information about the build environment and the
  PKGBUILD the package is built from. This check reports an issue whenever a
  built package is found that has no .BUILDINFO file.
'''

    name = 'pkgfile_missing_buildinfo'
    check_type = LinterCheckType.PKGENTRY

    header = 'built packages with no .BUILDINFO file'

    def check(self, pkgentry):
        ''' run the check '''
        if not pkgentry.pkgfile:
            return
        pkgfile = pkgentry.pkgfile

        if not pkgfile.buildinfo:
            raise LinterIssue(pkgfile, pkgfile.build_date)

    def format(self, issues):
        ''' format the list of found issues '''
        result = []
        for issue in issues:
            result.append('    %s (built %s)' % (issue[0], issue[1]))
        return "\n".join(sorted(result))


# pylint: disable=no-self-use
class PkgFileBadPkgbuildDigest(LinterCheckBase):
    '''
  for the list of built packages in the repos, check whether the PKGBUILD digest
  stored in its .BUILDINFO matches the digest of the PKGBUILD file in abslibre.
  This check reports an issue whenever a mismatch is found between the PKGBULID
  digest stored in the package file and the PKGBUILD in abslibre.
'''

    name = 'pkgfile_bad_pkgbuild_digest'
    check_type = LinterCheckType.PKGENTRY

    header = 'built packages with mismatched PKGBUILD digests'

    def check(self, pkgentry):
        ''' run the check '''
        if not pkgentry.pkgfile:
            return
        pkgfile = pkgentry.pkgfile
        if not pkgfile.buildinfo:
            return

        if not pkgentry.pkgbuilds:
            return
        pkgbuild = pkgentry.pkgbuilds[0]

        with open(pkgbuild.path, 'rb') as infile:
            pkgbuild_sha = hashlib.sha256(infile.read()).hexdigest()

        if pkgfile.buildinfo['pkgbuild_sha256sum'] != pkgbuild_sha:
            raise LinterIssue(pkgfile, pkgfile.build_date)

    def format(self, issues):
        ''' format the list of found issues '''
        result = []
        for issue in issues:
            result.append('    %s (built %s)' % (issue[0], issue[1]))
        return "\n".join(sorted(result))

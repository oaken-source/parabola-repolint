'''
these are linter checks for PKGBUILD / .pkg.tar.xz / repo.db entry integrity
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


KNOWN_ARCHES = CONFIG.parabola.arches


class InvalidPkgbuild(LinterCheckBase):
    '''
  this check tests for syntactical problems with the PKGBUILD file itself,
  basically anything that makepkg would choke on. It reports an issue whenever a
  PKGBUILD file is found in the repo that does not produce a valid output when
  processed with `makepkg --printsrcinfo`.
'''

    name = 'invalid_pkgbuild'
    check_type = LinterCheckType.PKGBUILD

    header = 'invalid PKGBUILDs'

    # pylint: disable=no-self-use
    def check(self, pkgbuild):
        ''' run the check '''
        if not pkgbuild.valid:
            raise LinterIssue('%s', pkgbuild)


class UnsupportedArches(LinterCheckBase):
    '''
  this check tests for PKGBUILD files that list archictectures in the `arch`
  array, that are not officially supported by parabola. This includes
  architectures that may have been supported in the past, but have since been
  dropped. The list of supported architectures is configurable in
  `parabola-repolint.conf` under the setting `parabola.arches`. The default
  setting is `('x86_64', 'i686', 'armv7h', 'ppc64le')`, which are, as of this
  writing, the architectures supported by parabola.
'''

    name = 'unsupported_arches'
    check_type = LinterCheckType.PKGBUILD

    header = 'PKGBUILDs with unsupported arches'

    # pylint: disable=no-self-use
    def check(self, pkgbuild):
        ''' run the check '''
        if not pkgbuild.valid:
            return

        unsup = {}

        unsup_base = pkgbuild.arches.difference(KNOWN_ARCHES, ['any'])
        if unsup_base:
            unsup['pkgbase'] = unsup_base

        for arch in pkgbuild.srcinfo:
            for pkgname, pkginfo in pkgbuild.srcinfo[arch].pkginfo.items():
                if 'arch' not in pkginfo:
                    continue
                unsup_pkg = pkginfo['arch'].difference(unsup_base, KNOWN_ARCHES, ['any'])
                if unsup_pkg:
                    if pkgname not in unsup:
                        unsup[pkgname] = set()
                    unsup[pkgname] = unsup[pkgname].union(unsup_pkg)

        if unsup:
            unsup_str = '; '.join(['%s: %s' % (p, ','.join(u)) for p, u in unsup.items()])
            raise LinterIssue('%s (%s)', pkgbuild, unsup_str)

'''
linter checks for repo dependency integrity
'''

import operator

from parabola_repolint.repocache import PkgVersion
from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


class UnsatisfiableDepends(LinterCheckBase):
    '''
  for the list of entries in the repo.db's check that all entries in the
  depends() array of the package are satisfiable with the provides() entries of
  the packages in the repositories core, extra, community, and the ones
  configured in CONFIG.parabola.repos. This check reports an issue whenever a
  depends() entry is found that is not satisfiable.
'''

    name = 'unsatisfiable_depends'
    check_type = LinterCheckType.PKGENTRY

    header = 'repo.db entries with unsatisfiable depends'

    def check(self, pkgentry):
        ''' run the check '''
        repos = list(self._cache.repos.values()) + list(self._cache.arch_repos.values())
        missing = []

        for depend in pkgentry.depends:
            matches = self._repos_contain_depends(depend, repos, pkgentry.arch)
            if not matches:
                missing.append(depend)

        if missing:
            raise LinterIssue('%s (%s)', pkgentry, ','.join(missing))

    def _repos_contain_depends(self, depend, repos, arch):
        ''' test whether a dependency is provided by the list of repos '''
        version = None
        splits = ['==', '>=', '<=', '>', '<', '=']
        for split in splits:
            if split in depend:
                depend, version = depend.split(split)
                version = (split, PkgVersion(version))
                break

        candidates = []
        for repo in repos:
            candidates += repo.provides_cache.get(arch, {}).get(depend, [])

        matches = []
        for candidate in candidates:
            if self._candidate_contains_depends(depend, candidate, version):
                matches.append(candidate)

        return matches

    def _candidate_contains_depends(self, depend, candidate, version):
        ''' test whether a dependency is provided by a pkgentry '''
        if version is None:
            return True

        provides = candidate.provides.union([candidate.pkgname])
        pversion = candidate.pkgver

        for provide in provides:
            assert '<' not in provide
            assert '>' not in provide

            if '=' not in provide:
                continue

            provide, _pversion = provide.split('=')
            if provide == depend:
                pversion = PkgVersion(_pversion)
                break

        operators = {
            '==': operator.eq,
            '=':  operator.eq,
            '>=': operator.ge,
            '<=': operator.le,
            '>':  operator.gt,
            '<':  operator.lt,
        }

        return operators[version[0]](pversion, version[1])

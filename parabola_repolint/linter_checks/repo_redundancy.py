'''
these are checks for things in the repo that are redundant and can go away.
'''

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class RedundantPkgEntryPCR(LinterCheckBase):
    '''
  for the list of entries in the parabola repos, check whether package is
  redundant, meaning an entry of the same name exists in one of the arch repos
  (currently core, extra and community). The check reports an issue whenever a
  redundant entry in a repo.db is found.
'''

    name = 'redundant_pkgentry_pcr'
    check_type = LinterCheckType.PKGENTRY

    header = 'redundant packagess in [pcr]'

    def check(self, pkgentry):
        ''' run the check '''
        if pkgentry.repo.name != 'pcr':
            return

        for repo in self._cache.arch_repos.values():
            if repo.pkgentries_cache.get(pkgentry.arch, []).get(pkgentry.pkgname, None):
                raise LinterIssue('%s (in %s)', pkgentry, repo.name)

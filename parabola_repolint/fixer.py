'''
this module provides the linter issue autofixer
'''

import os
import sh
import logging

from parabola_repolint.config import CONFIG


class Fixer():
    ''' the master fixer class '''

    def __init__(self, repo_cache):
        ''' constructor '''
        self._cache = repo_cache

    def run_fixes(self, checks):
        ''' run the fixes for the given issues '''
        for check in checks:
            base_path = os.path.join(CONFIG.fixhooks.scriptroot, str(check))
            if not os.path.exists(base_path):
                continue

            for issue in check.issues:
                fixbase = check.fixhook_base(issue)
                fixargs = check.fixhook_args(issue)

                path = os.path.join(base_path, fixbase)
                if not os.path.exists(path):
                    continue

                try:
                    sh.bash(path, fixbase, fixargs, _cwd=CONFIG.fixhooks.abslibre)
                except sh.ErrorReturnCode:
                    logging.exception('%s fixhook failed for %s (%s)', check, fixbase, ', '.join(fixargs))

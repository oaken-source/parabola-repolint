'''
parabola repo functions
'''

import logging
import sh
from .config import CONFIG


def update_repo():
    ''' attempt to update the repo and check for outdated packages '''
    logging.info('updating repo at %s', CONFIG.parabola.repo_path)
    sh.git.pull(
        _cwd=CONFIG.parabola.repo_path,
        _out=lambda l: logging.info(l.rstrip())
    )

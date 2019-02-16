'''
globally accessible gpg wrappers
'''

from urllib.parse import unquote
import logging

import gnupg

from parabola_repolint.config import CONFIG


GPG_PACMAN = gnupg.GPG(gnupghome=CONFIG.gnupg.gpgdir)
GPG_HOME = gnupg.GPG()


def get_uid(key_id):
    ''' attempt to produce a uid from a key id '''
    key = GPG_HOME.search_keys(key_id, CONFIG.gnupg.keyserver)
    if key.uids:
        return unquote(key.uids[0])
    logging.warning('%s: error in key resolution: (%s)', key_id, key.__dict__)
    return key_id

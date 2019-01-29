'''
this is a linter check for invalid package signatures
'''

import logging

import gnupg

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.config import CONFIG


# pylint: disable=no-self-use
class InvalidSignature(LinterCheckBase):
    ''' check for a package without an invalid signature '''

    name = 'invalid_signature'
    check_type = LinterCheckType.PACKAGE

    def __init__(self, *args, **kwargs):
        ''' constructor '''
        super().__init__(*args, **kwargs)
        self._gpg_pacman = gnupg.GPG(gnupghome=CONFIG.gnupg.gpgdir)
        self._gpg_home = gnupg.GPG()

    def check(self, package):
        ''' check for packages with an invalid signature '''
        sigfile = "%s.sig" % package.path
        try:
            with open(sigfile, 'rb') as sig:
                self._check_sigfile(package, sig)
        except IOError:
            raise LinterIssue(package, 'missing signature')

    def _check_sigfile(self, package, sig):
        ''' check whether signature and package match '''
        verify = self._gpg_pacman.verify_file(sig, package.path)
        if not verify.valid:
            uid = verify.key_id
            key = self._gpg_home.search_keys(uid, CONFIG.gnupg.keyserver)
            if key.uids:
                uid = key.uids[0]
            else:
                logging.warning('%s: error in key resolution: (%s)', uid, key.__dict__)
            if verify.key_status == 'signing key has expired':
                raise LinterIssue(package, 'signing key has expired (%s)' % uid)
            if verify.status == 'no public key':
                raise LinterIssue(package, 'no public key: %s' % uid)
            logging.warning('%s: unknown gpg invalidity: %s', package, verify.__dict__)
            raise LinterIssue(package, 'invalid signature')

    def format(self, issues):
        ''' format the list of found issues '''
        result = 'packages with invalid signatures:'
        for issue in issues:
            result += '\n    %s: %s' % (issue[0], issue[1])
        return result

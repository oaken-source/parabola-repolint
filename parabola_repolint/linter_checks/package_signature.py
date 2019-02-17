'''
this are linter checks for package signatures
'''

import logging
import datetime

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType
from parabola_repolint.gnupg import GPG_PACMAN, get_uid


# pylint: disable=no-self-use
class KeyExpiryImminent(LinterCheckBase):
    '''
  for the list of keys in parabola.gpg, check whether they are expired, or are
  about to expire. This check reports an issue for any expired key in the
  keyring, as well as any key that is going to expire within the next 90 days,
  indicating that the key should be extended and the keyring rebuilt to avoid
  user-facing issues on system updates.
'''

    name = 'key_expiry_imminent'
    check_type = LinterCheckType.KEYRING

    header = 'keyring entries expired or about to expire'

    def check(self, key):
        ''' run the check '''
        if not key['expires']:
            return

        expires = datetime.datetime.utcfromtimestamp(int(key['expires']))
        time = expires.strftime("%Y-%m-%d")

        if expires < datetime.datetime.now():
            raise LinterIssue(get_uid(key['keyid']), 'expired %s' % time)
        if expires <= datetime.datetime.now() + datetime.timedelta(days=90):
            raise LinterIssue(get_uid(key['keyid']), 'expires %s' % time)

    def format(self, issues):
        ''' format the list of found issues '''
        result = []
        for issue in issues:
            result.append('    %s (%s)' % (issue[0], issue[1]))
        return "\n".join(sorted(result))


# pylint: disable=no-self-use
class InvalidSignature(LinterCheckBase):
    '''
  this check validates the package signature against the pacman keyrings. It
  reports an issue whenever a package is signed by an unknown key, that is not
  part of the keyring, or by a key that has expired.
'''

    name = 'invalid_signature'
    check_type = LinterCheckType.PKGFILE

    header = 'packages with invalid signatures'

    def check(self, package):
        ''' run the check '''
        sigfile = "%s.sig" % package.path
        try:
            with open(sigfile, 'rb') as sig:
                self._check_sigfile(package, sig)
        except IOError:
            raise LinterIssue(package, 'missing signature')

    def _check_sigfile(self, package, sig):
        ''' check whether signature and package match '''
        verify = GPG_PACMAN.verify_file(sig, package.path)
        if not verify.valid:
            uid = get_uid(verify.key_id)
            if verify.key_status == 'signing key has expired':
                raise LinterIssue(package, 'signing key has expired (%s)' % uid)
            if verify.status == 'no public key':
                raise LinterIssue(package, 'no public key: %s' % uid)
            logging.warning('%s: unknown gpg invalidity: %s', package, verify.__dict__)
            raise LinterIssue(package, 'invalid signature')

    def format(self, issues):
        ''' format the list of found issues '''
        result = []
        for issue in issues:
            result.append('    %s: %s' % (issue[0], issue[1]))
        return "\n".join(sorted(result))

'''
this are linter checks for package signatures
'''

import base64
import logging
import datetime

from parabola_repolint.linter import LinterIssue, LinterCheckBase, LinterCheckType


# pylint: disable=no-self-use
class SigningKeyExpiry(LinterCheckBase):
    '''
  for the list of signing keys and subkeys in parabola.gpg that are used to sign
  packages in the repos, check whether they are expired, or are about to expire.
  This check reports an issue for any expired signing key in the keyring, as well
  as any key that is going to expire within the next 90 days, indicating that the
  key should be extended and the keyring rebuilt to avoid user-facing issues on
  system updates.
'''

    name = 'signing_key_expiry'
    check_type = LinterCheckType.SIGNING_KEY

    header = 'signing keys expired or about to expire'

    def check(self, key):
        ''' run the check '''
        if not key['packages']:
            return
        if not key['expires']:
            return

        expires = datetime.datetime.utcfromtimestamp(int(key['expires']))
        time = expires.strftime("%Y-%m-%d")

        reason = None

        if expires < datetime.datetime.now():
            reason = 'expired %s' % time
        elif expires <= datetime.datetime.now() + datetime.timedelta(days=90):
            reason = 'expires %s' % time

        if reason is not None:
            if 'master_key' in key:
                reason += ' (subkey of %s)' % key['master_key']
            raise LinterIssue('%s: %s (signed %i)', key['keyid'], reason, len(key['packages']))


# pylint: disable=no-self-use
class MasterKeyExpiry(LinterCheckBase):
    '''
  for the list of master keys in parabola.gpg, check whether they are expired, or
  are about to expire. This check reports an issue for any expired master key in
  the keyring, as well as any key that is going to expire within the next 90
  days, indicating that the key should be extended and the keyring rebuilt to
  avoid user-facing issues on system updates.
'''

    name = 'master_key_expiry'
    check_type = LinterCheckType.MASTER_KEY

    header = 'master keys expired or about to expire'

    def check(self, key):
        ''' run the check '''
        if not key['expires']:
            return

        expires = datetime.datetime.utcfromtimestamp(int(key['expires']))
        time = expires.strftime("%Y-%m-%d")

        reason = None

        if expires < datetime.datetime.now():
            reason = 'expired %s' % time
        elif expires <= datetime.datetime.now() + datetime.timedelta(days=90):
            reason = 'expires %s' % time

        if reason is not None:
            raise LinterIssue('%s: %s', key['keyid'], reason)


# pylint: disable=no-self-use
class PkgEntrySignatureMismatch(LinterCheckBase):
    '''
  for the list of entries in the repo.db's, check whether the signature stored in
  the repository matches the signature stored in the detached signature file of
  the corresponding built package. This check reports an issue whenever the
  signature in the repo.db reports a different key then what was used to produce
  the built package signature.
'''

    name = 'pkgentry_signature_mismatch'
    check_type = LinterCheckType.PKGENTRY

    header = 'repo.db entries with mismatched signing keys'

    def check(self, pkgentry):
        ''' run the check '''
        if not pkgentry.pkgfile:
            return

        key1 = pkgentry.pkgfile.siginfo['key_id'].upper()
        key2 = base64.b64decode(pkgentry.pgpsig)

        # quick & dirty gpg packet parser
        # https://tools.ietf.org/search/rfc4880
        header = key2[0]
        assert header & 0x80 == 0x80
        assert header & 0x40 == 0x00
        assert header & 0x03 == 0x01
        assert header & 0x1C == 0x08

        version = key2[3]
        assert version == 0x04

        hashed_len = key2[7] * 256 + key2[8]
        unhashed_len = key2[9 + hashed_len] * 256 + key2[10 + hashed_len]

        data = key2[11 + hashed_len:11 + hashed_len + unhashed_len]
        assert data[1] == 0x10 # issuer
        key2 = data[2:10].hex().upper()

        if key1 != key2:
            raise LinterIssue('%s: %s != %s', pkgentry, key1, key2)


# pylint: disable=no-self-use
class PkgFileInvalidSignature(LinterCheckBase):
    '''
  this check validates the package signature against the pacman keyrings. It
  reports an issue whenever a package is signed by an unknown key, that is not
  part of the keyring, or by a key that has expired.
'''

    name = 'pkgfile_invalid_signature'
    check_type = LinterCheckType.PKGFILE

    header = 'packages with invalid signatures'

    def check(self, package):
        ''' run the check '''
        verify = package.siginfo

        key = self._cache.key_cache.get(verify['key_id'], None)
        if key is None:
            raise LinterIssue('%s: no public key: %s', package, verify['key_id'])

        if key['expires']:
            expires = datetime.datetime.utcfromtimestamp(int(key['expires']))
            if expires < datetime.datetime.now():
                raise LinterIssue('%s: signing key expired (%s)', package, verify['key_id'])

        if not verify['valid']:
            # if this is triggered, add more cases here.
            logging.warning('%s: unknown gpg invalidity: %s', package, verify)
            raise LinterIssue('%s: invalid signature', package)

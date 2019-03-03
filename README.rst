
parabola-repolint
=================

this is a set of automated integrity checks on the parabola repositories. The
checks operate on the repository of PKGBUILD files, and the package files
distributed on the mirrors, in order to spot inconsistencies, installation
problems, and runtime issues early and reliably, even for lesser used packages.

The list of implemented checks is outlined below, with more checks to be added.

built package integrity checks
------------------------------

a number of checks for basic .pkg.tar.xz integrity

pkgfile_missing_buildinfo
~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages in the repos, check whether each has an embedded
.BUILDINFO file, containing information about the build environment and the
PKGBUILD the package is built from. This check reports an issue whenever a
built package is found that has no .BUILDINFO file.

pkgfile_missing_pkginfo
~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages in the repos, check whether each has an embedded
.PKGINFO file, containing information about the package. This check reports an
issue whenever a built package is found that has no .PKGINFO file.

pkgfile_bad_pkgbuild_digest
~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages in the repos, check whether the PKGBUILD digest
stored in its .BUILDINFO matches the digest of the PKGBUILD file in abslibre.
This check reports an issue whenever a mismatch is found between the PKGBULID
digest stored in the package file and the PKGBUILD in abslibre.

repository redundancy checks
----------------------------

a number of checks for redundant entries in the repositories

redundant_pkgentry_pcr
~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in the parabola repos, check whether package is
redundant, meaning an entry of the same name exists in one of the arch repos
(currently core, extra and community). The check reports an issue whenever a
redundant entry in a repo.db is found.

repository integrity checks
---------------------------

a number of checks validating the consistency of the relationships between
repo.db entries, package files and PKGBUILD recipes

pkgbuild_missing_pkgentries
~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of packages produced by the pkgbuild for the supported arches,
check whether an entry in a repo.db exists for each of them. The check reports
an issue whenever a repo.db entry is missing for a package that should be
produced.

pkgbuild_duplicate_pkgentries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of packages produced by the pkgbuild for the supported arches,
check whether duplicate entries in a repo.db exists for each of them. The check
reports an issue whenever more than one repo.db entry exists for a package that
should produced by the PKGBUILD.

pkgbuild_missing_pkgfiles
~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of packages produced by the pkgbuild for the supported arches,
check whether a package file exists for each of them. The check reports an
issue whenever a package file is missing for a package that should be produced.

pkgentry_missing_pkgbuild
~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in a repo.db, check whether a valid PKGBUILD exists
that creates the entry. The check reports an issue for each repo.db entry that
has no producing PKGBUILD.

pkgentry_duplicate_pkgbuilds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in a repo.db, check whether more than one valid
PKGBUILD exists that creates the entry. The check reports an issue for each
repo.db entry that has more than one producing PKGBUILD.

pkgentry_missing_pkgfile
~~~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in a repo.db, check wether a built package exists that
backs the entry. The check reports an issue for each repo.db entry that is not
associatable with a valid built package.

pkgfile_missing_pkgbuild
~~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages, check whether a valid PKGBUILD exists that
creates the package. The check reports an issue for each built package that has
no producing PKGBUILD.

pkgfile_duplicate_pkgbuilds
~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages, check whether more than one valid PKGBUILD
exists that creates the package. The check reports an issue for each built
package that has more than one producing PKGBUILD.

pkgfile_missing_pkgentry
~~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages, check wether a repo.db entry exists that refers
to the package. The check reports an issue for each built package that is not
referred to by a repo.db entry.

pkgfile_duplicate_pkgentries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of built packages, check that at most one repo.db entry exists
that refers to the package. The check reports an issue for each built package
that is referred to by multiple repo.db entries.

PKGBUILD validity checks
------------------------

a number of checks validating PKGBUILD properties

invalid_pkgbuild
~~~~~~~~~~~~~~~~

this check tests for syntactical problems with the PKGBUILD file itself,
basically anything that makepkg would choke on. It reports an issue whenever a
PKGBUILD file is found in the repo that does not produce a valid output when
processed with `makepkg --printsrcinfo`.

unsupported_architecture
~~~~~~~~~~~~~~~~~~~~~~~~

this check tests for PKGBUILD files that list archictectures in the `arch`
array, that are not officially supported by parabola. This includes
architectures that may have been supported in the past, but have since been
dropped. The list of supported architectures is configurable in
`parabola-repolint.conf` under the setting `parabola.arches`. The default
setting is `('x86_64', 'i686', 'armv7h', 'ppc64le')`, which are, as of this
writing, the architectures supported by parabola.

package signature checks
------------------------

a number of checks validating package signatures and keyring entries

signing_key_expiry
~~~~~~~~~~~~~~~~~~

for the list of signing keys and subkeys in parabola.gpg that are used to sign
packages in the repos, check whether they are expired, or are about to expire.
This check reports an issue for any expired signing key in the keyring, as well
as any key that is going to expire within the next 90 days, indicating that the
key should be extended and the keyring rebuilt to avoid user-facing issues on
system updates.

master_key_expiry
~~~~~~~~~~~~~~~~~

for the list of master keys in parabola.gpg, check whether they are expired, or
are about to expire. This check reports an issue for any expired master key in
the keyring, as well as any key that is going to expire within the next 90
days, indicating that the key should be extended and the keyring rebuilt to
avoid user-facing issues on system updates.

pkgentry_signature_mismatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in the repo.db's, check whether the signature stored in
the repository matches the signature stored in the detached signature file of
the corresponding built package. This check reports an issue whenever the
signature in the repo.db reports a different key then what was used to produce
the built package signature.

pkgfile_invalid_signature
~~~~~~~~~~~~~~~~~~~~~~~~~

this check validates the package signature against the pacman keyrings. It
reports an issue whenever a package is signed by an unknown key, that is not
part of the keyring, or by a key that has expired.

package dependency checks
-------------------------

a number of checks verifying the satisfiability of dependencies in the repos

unsatisfiable_depends
~~~~~~~~~~~~~~~~~~~~~

for the list of entries in the repo.db's check that all entries in the
depends() array of the package are satisfiable with the provides() entries of
the packages in the repositories core, extra, community, and the ones
configured in CONFIG.parabola.repos. This check reports an issue whenever a
depends() entry is found that is not satisfiable.

unsatisfiable_makedepends
~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in the repo.db's check that all entries in the
makedepends() array of the package are satisfiable with the provides() entries
of the packages in the repositories core, extra, community, and the ones
configured in CONFIG.parabola.repos. This check reports an issue whenever a
makedepends() entry is found that is not satisfiable.

unsatisfiable_checkdepends
~~~~~~~~~~~~~~~~~~~~~~~~~~

for the list of entries in the repo.db's check that all entries in the
checkdepends() array of the package are satisfiable with the provides() entries
of the packages in the repositories core, extra, community, and the ones
configured in CONFIG.parabola.repos. This check reports an issue whenever a
checkdepends() entry is found that is not satisfiable.

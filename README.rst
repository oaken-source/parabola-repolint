
parabola-repolint
=================

this is a set of automated integrity checks on the parabola repositories. The
checks operate on the repository of PKGBUILD files, and the package files
distributed on the mirrors, in order to spot inconsistencies, installation
problems, and runtime issues early and reliably, even for lesser used packages.

The list of implemented checks is outlined below, with more checks to be added.

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

a number of checks validating package signatures

invalid_checksum
~~~~~~~~~~~~~~~~

this check validates the package signature against the pacman keyrings. It
reports an issue whenever a package is signed by an unknown key, that is not
part of the keyring, or by a key that has expired.

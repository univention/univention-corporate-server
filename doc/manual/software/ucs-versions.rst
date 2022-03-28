.. _computers-differentiation-of-update-variants-ucs-versions:

Differentiation of update variants / UCS versions
=================================================

Four types of UCS updates are differentiated:

Major releases
   *Major releases* appear approximately every three to four years. Major
   releases can differ significantly from previous major releases in terms of
   their scope of services, functioning and the software they contain.

Minor releases
   During the maintenance period of a major release, *minor releases* are
   released approximately every 10-12 months. These updates include corrections
   to recently identified errors and the expansion of the product with
   additional features. At the same time and as far as this is possible, the
   minor releases are compatible with the previous versions in terms of their
   functioning, interfaces and operation. Should a change in behavior prove
   practical or unavoidable, this will be noted in the release notes when the
   new version is published.

Patchlevel releases
   *Patchlevel releases* are released approximately every three months and
   combine all errata updates published until then.

Errata updates
   Univention continuously releases *errata updates*. Errata updates provide
   fixes for security vulnerabilities and bugfixes/smaller enhancements to make
   them available to customer systems quickly. An overview of all errata updates
   can be found at https://errata.software-univention.de/.

Every released UCS version has an unambiguous version number; it is composed of
a figure (the major version), a full stop, a second figure (the minor version),
a hyphen and a third figure (the patch level version). The version UCS 4.2-1
thus refers to the first patch level update for the second minor update for the
major release UCS 4.

The *pre-update script* :file:`preup.sh` is run before every release update. It
checks for example whether any problems exist, in which case the update is
canceled in a controlled manner. The *post-update script* :file:`postup.sh` is
run at the end of the update to perform additional cleanups, if necessary.

Errata updates always refer to certain minor releases, e.g., for UCS 5.0. Errata
updates can generally be installed for all patch level versions of a minor
release.

If a new release or errata updates are available, a corresponding notification
is given when a user opens a UMC module. The availability of new updates is also
notified via e-mail; the corresponding newsletters - separated into release and
error updates - can be subscribed on the Univention website. A changelog
document is published for every release update listing the updated packages,
information on error corrections and new functions and references to the
Univention Bugzilla.

.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

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
   fixes for security vulnerabilities, bug fixes, and smaller enhancements to make
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
notified via email; the corresponding newsletters - separated into release and
error updates - can be subscribed on the Univention website. A changelog
document is published for every release update listing the updated packages,
information on error corrections and new functions and references to the
Univention Bugzilla.

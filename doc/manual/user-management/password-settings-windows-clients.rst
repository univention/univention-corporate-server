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

.. _users-password-samba:

Password settings for Windows clients when using Samba
======================================================

With the Samba domain object, one can set the password requirements for
logins to Windows clients in a Samba domain.

The Samba domain object is managed via the UMC module :guilabel:`LDAP
directory`. It can be found in the ``samba``
container below the LDAP base and carries the domain's NetBIOS name.

The settings of the Samba domain object and the policy (see :ref:`users-passwords`) should be set identically,
otherwise different password requirements will apply for logins to
Windows and UCS systems.

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Password length
     - The minimum number of characters for a user password.

   * - Password history
     - The latest password changes are saved in the form of hashes. These
       passwords can then not be used by the user as a new password when setting
       a new password. With a password history of five, for example, five new
       passwords must be set before a password can be reused.

   * - Minimum password age
     - The period of time set for this must have at least expired since the last
       password change before a user can reset their password again.

   * - Maximum password age
     - Once the saved period of time has elapsed, the password must be changed
       again by the user the next time they sign in. If the value is left blank,
       the password is infinitely valid.

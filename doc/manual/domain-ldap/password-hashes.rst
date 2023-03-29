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

.. _domain-password-hashes:

Password hashes in the directory service
========================================

User password hashes are stored in the directory service in the ``userPassword``
attribute. The :program:`crypt` library function is used to hash passwords. The
actual hashing method can be configured via the |UCSUCRV|
:envvar:`password/hashing/method`, ``SHA-512`` is used by default.

As an alternative |UCSUCS| (from version :uv:erratum:`4.4x887` on) offers the
option of using :program:`bcrypt` as hashing method for passwords of user
accounts. To activate :program:`bcrypt` support in OpenLDAP the |UCSUCRV|
:envvar:`ldap/pw-bcrypt` has to bet set to ``true`` on all LDAP servers.
Otherwise it is not possible authenticate with a :program:`bcrypt` hash as
password hash. Additionally the |UCSUCRV| :envvar:`password/hashing/bcrypt` has
to be set to ``true``, again on all servers, to activate :program:`bcrypt` as
the hashing method for setting or changing user password.

In addition, the :program:`bcrypt` cost factor and the
:program:`bcrypt` variant can be configured via the
|UCSUCRV|\ s :envvar:`password/hashing/bcrypt/cost_factor` (default
``12``) and :envvar:`password/hashing/bcrypt/prefix` (default ``2b``).

.. caution::

   :program:`bcrypt` is limited to a maximum of 72 characters. So only the first
   72 characters of the password are used to generate the hashes.

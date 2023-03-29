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

.. _join-run:

Running join scripts
====================

.. index::
   single: domain join; running

The following commands related to running join scripts exist:

:command:`univention-join`
   When :command:`univention-join` is invoked, the machine account is created, if
   it is missing. Otherwise an already existing account is re-used which allows
   it to be created beforehand. The distinguished name (dn) of that entry is
   stored locally in the |UCSUCRV| :envvar:`ldap/hostdn`. A random password is
   generated, which is stored in the file :file:`/etc/machine.secret`.

   After that the file :file:`/var/univention-join/status` is cleared and all
   join scripts located in :file:`/usr/lib/univention-install/` are executed in
   lexicographical order.

:command:`univention-run-join-scripts`
   This command is similar to :command:`univention-join`, but skips the first
   step of creating a machine account. Only those join scripts are executed,
   whose current version is not yet registered in
   :file:`/var/univention-join/status`.

:command:`univention-check-join-status`
   This command only checks for join scripts in
   :file:`/usr/lib/univention-install/`, whose version is not yet registered in
   :file:`/var/univention-join/status`.

When packages are installed, it depends on the server role, if join scripts are
invoked automatically from the ``postinst`` Debian maintainer script or not.
This only happens on |UCSPRIMARYDN| and |UCSBACKUPDN| system roles, where the
local ``root`` user has access to the file containing the LDAP credentials. On
all other system roles the join scripts need to be run manually by invoking
:command:`univention-run-join-scripts` or doing so through UMC.

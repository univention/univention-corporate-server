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

.. _system-roles:

UCS system roles
================

In a UCS domain systems can be installed in different *system roles*. The
following gives a short characterization of the different systems.

.. _domain-ldap-primary-directory-node:

|UCSPRIMARYDN|
--------------

A system with the |UCSPRIMARYDN| role is the primary domain controller of a UCS
domain and is always installed as the first system. The domain data (such as
users, groups, printers) and the SSL security certificates are saved on the
|UCSPRIMARYDN|.

Copies of these data are automatically transferred to all servers with the
|UCSBACKUPDN| role.

.. _domain-ldap-backup-directory-node:

|UCSBACKUPDN|
-------------

All the domain data and SSL security certificates are saved as read-only copies
on servers with the |UCSBACKUPDN| role.

The |UCSBACKUPDN| is the fallback system for the |UCSPRIMARYDN|. If the latter
should fail, a |UCSBACKUPDN| can take over the role of the |UCSPRIMARYDN|
permanently (see :ref:`domain-backup2master`).

.. _domain-ldap-replica-directory-node:

|UCSREPLICADN|
--------------

All the domain data are saved as read-only copies on servers with the
|UCSREPLICADN| role. In contrast to the |UCSBACKUPDN|, however, not all security
certificates are synchronized.

As access to the services running on a |UCSREPLICADN| are performed against the
local LDAP server, |UCSREPLICADN|\ s are ideal for site servers and the
distribution of load-intensive services.

A |UCSREPLICADN| cannot be promoted to a |UCSPRIMARYDN|.

.. _domain-ldap-managed-node:

|UCSMANAGEDNODE|
----------------

|UCSMANAGEDNODE| are server systems without a local LDAP server. Access to
domain data here is performed via other servers in the domain.

.. _domain-ldap-ubuntu:

Ubuntu
------

Ubuntu clients can be managed with this system role, see
:ref:`computers-ubuntu`.

.. _domain-ldap-linux:

Linux
-----

This system role is used for the integration of other Linux systems than UCS and
Ubuntu, e.g., for Debian or CentOS systems. The integration is documented in
:cite:t:`ext-doc-domain`.

.. _domain-ldap-macos:

macOS
-----

macOS systems can be joined into a UCS domain using Samba/AD. Additional
information can be found in :ref:`macos-domain-join`.

.. _domain-ldap-domain-trust-account:

Domain Trust Account
--------------------

A domain trust account is set up for trust relationships between Windows and UCS
domains.

.. _domain-ldap-ip-managed-client:

IP client
---------

An IP client allows the integration of non-UCS systems into the IP management
(DNS/DHCP), e.g., for network printers or routers.

.. _domain-ldap-windows-domain-controller:

Windows Domaincontroller
------------------------

Windows domain controllers in a Samba/AD environment are operated with this
system role.

.. _domain-ldap-windows-workstation-server:

Windows Workstation/Server
--------------------------

Windows clients and Windows |UCSMANAGEDNODE|\ s are managed with this system
role.

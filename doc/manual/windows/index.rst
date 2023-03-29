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

.. _windows-services-for-windows:

********************
Services for Windows
********************

UCS can offer Active Directory (AD) services, be a member of an Active Directory
domain or synchronize objects between Active Directory domains and a UCS domain.

For the purposes of Windows systems, UCS can assume the tasks of Windows server
systems:

* Domain controller function / authentication services

* File services

* Print services

In UCS all these services are provided by Samba.

UCS supports the mostly automatic migration of an existing Active Directory
domain to UCS. All users, groups, computer objects and group policies are
migrated without the need to rejoin the Windows clients. This is documented in
:ref:`windows-ad-takeover`.

Microsoft Active Directory domain controllers cannot join the Samba domain. This
functionality is planned at a later point in time.

Samba can not join an Active Directory Forest yet at this point.

Incoming trust relationships with other Active Directory domains are
configurable. In this setup the external Active Directory domain trusts
authentication decisions of the UCS domain (Windows trusts UCS) so that UCS
users can sign in to systems and Active Directory backed services in the Windows
domain (see :ref:`windows-trust`). Outgoing trusts with Active Directory domain
(UCS trusts Windows) are not supported currently.

.. toctree::
   :caption: Chapter contents:

   samba-domain
   ad-connection
   ad-takeover
   trust

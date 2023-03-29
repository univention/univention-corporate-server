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

.. _delegated-administration:

Delegated administration for UMC modules
========================================

By default only the members of the ``Domain Admins`` group can access all UMC
modules. Policies can be used to configure the access to UMC modules for groups
or individual users. For example, this can be used to assign a helpdesk team the
authority to manage printers without giving them complete access to the
administration of the domain.

UMC modules are assigned via a *UMC* policy which can be assigned to user and
group objects. The evaluation is performed additively, i.e., general access
rights can be assigned via ACLs assigned to groups and these rights can be
extended via ACLs bound to user (see :ref:`central-policies`).

In addition to the assignment of UMC policies, LDAP access rights need to be
taken into account, as well, for modules that manage data in the LDAP directory.
All LDAP modifications are applied to the whole UCS domain. Therefore by default
only members of the ``Domain Admins`` group and some internally used accounts
have full access to the UCS LDAP. If a module is granted via a UMC policy, the
LDAP access must also be allowed for the user/group in the LDAP ACLs. Further
information on LDAP ACLs can be found in :ref:`domain-ldap-acls`.

.. list-table:: Policy *UMC*
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - List of allowed UCS operation sets
     - All the UMC modules defined here are displayed to the user or group to
       which this ACL is applied. The names of the domain modules begin with
       ``UDM``.

.. caution::

   For access to UMC modules, only policies are considered that are assigned to
   groups or directly to user and computer accounts. Nested group memberships
   (i.e., groups in groups) are not evaluated.

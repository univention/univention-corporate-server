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

.. _concept-domain:

Domain concept
==============

.. index::
   single: user
   pair: group; user group
   single: identity management; system
   single: service
   single: trust context
   single: domain; service

The domain concept is the most important concept in an IT environment operated
with |UCS|. The domain concept offers a way to centrally manage an IT
environment where administrators can map their organization's structure to the
IT environment.

Simplified, an IT environment consists of computer systems and users. Systems
offer services that provide capability. Users use capability. A domain is
a single trust context that groups one or more entities like computer systems or
users. The domain offers special services called domain services to systems and
users. :numref:`fig-concepts-domain-systems-users` shows the relationship
between the actors systems, services, and users.

.. _fig-concepts-domain-systems-users:

.. figure:: /images/Systems-and-users-in-domain.*

   Relationship of the *systems*, *services* and *users* in a domain

A trust context uses roles, permissions, and cryptographic certificates to ensure
secure communication between the domain participants. Domain services and domain
participants can rely on the shared trust context when secure and mutually
authenticated communication is required.

One key participant in a domain is the identity, a digital representation for
persons. An identity represents an account for a user in a domain. It holds
information like for example username and password for login. Furthermore, it
contains various data associated to the user like for example group memberships,
permissions, and different attributes used by services.

User accounts are organized in groups and users can belong to multiple groups.
User groups help administrators to apply permissions for domain services to
users and are essential to the organization's structure to the domain
administration.

All the objects in a domain need to be managed and organized. In a domain a
central database called domain database registers all objects, like for example
user identities, computer systems, printers, and file shares. See
:numref:`fig-concepts-domain-database` for a graphical interpretation. The
database stores the objects in a hierarchical tree-like structure. One or more
central systems store the central database and are called domain node.

.. _fig-concepts-domain-database:

.. figure:: /images/Domain-database.*

   Central domain database with different objects

UCS is a system that operates the central database for the domain. UCS is the
central platform that implements the domain concept and helps administrators to
manage and organize the IT environment for their organization. For the distinct
roles of UCS systems in a domain, see the :ref:`role concept <concept-role>`.

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

.. _concept-replication:

Replication concept
===================

The replication concept ensures the availability and consistency of the central
domain database and contributes to its scalability. It's necessary to keep the
domain data synchronized across all domain nodes because more than one domain
node can have a copy of the central database. For example, domain nodes can get
disconnected or need to shutdown for maintenance.

|UCS| implements the replication concept. The first domain node in the domain
has the following tasks:

* It writes domain object data to the database.
* It monitors changes to the database.
* It makes changes available to other domain nodes.

The other domain nodes have a read-only copy of the domain database.

.. TODO Activate reference once the section about domain replication is written in the listener part.

   What components are involved for replication and how it works in detail, see
   :ref:`services-listener-domain-replication`.

The replication synchronizes a lot of data types. The following list names a
few that domain nodes replicate and can't cover all items:

* User identities
* Groups
* Policies
* Permissions
* Information about systems
* Information about printers
* Information about file shares

The domain replication in UCS also ensures that the affected UCS systems run
follow-up actions after the changes are replicated. The actions can contain,
for example, updates to configurations of services and making the changes
available to the users.

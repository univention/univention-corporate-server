.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

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

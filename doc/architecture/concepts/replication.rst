.. _concept-replication:

Replication concept
===================

The replication concept ensures the availability and consistency of the central
domain database and contributes to its scalability. It is necessary to keep the
domain data synchronized across all domain controllers because more than one domain
controller can have a copy of the central database. For example single domain
controllers can get disconnected or need to shutdown for maintenance.

Univention Corporate Server (UCS) implements the replication concept. The first
domain controller in the domain has the following tasks:

* It writes domain object data to the database.
* It monitors changes to the database.
* It makes changes available to other domain controllers.

The other domain controllers have a read-only copy of the domain database.

.. TODO Activate reference once the section about domain replication is written in the listener part.

   What components are involved for replication and how it works in detail, see
   :ref:`services-listener-domain-replication`.

The replication synchronizes the following data types between domain
controllers:

* User identities
* Groups
* Policies
* Permissions
* Information about systems
* Information about printers
* Information about file shares

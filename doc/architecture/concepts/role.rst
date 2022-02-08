.. _concept-role:

Role concept
============

The role concept assigns different roles to the systems in a domain. Univention
Corporate Server (UCS) follows the role concept.

Primary Directory Node
----------------------

.. index::
   single: domain roles; Primary Directory Node
   single: Primary Directory Node

A UCS system with this role is the first, the primary, domain controller in a
domain. It is the only system with write permissions to the central domain
database. Only one system in the domain can have the Primary Directory Node
role.

Backup Directory Node
---------------------

.. index::
   single: domain roles; Backup Directory Node
   single: Backup Directory Node

A UCS system with this role has a complete read-only copy of the domain
database, including security certificates. More than one UCS system can have the
Backup Directory Node role. In case the Primary Directory Node is unavailable
and recovery is impossible, an administrator can promote a UCS system in the
role Backup Directory Node to a Primary Directory Node.

Replica Directory Node
----------------------

.. index::
   single: domain roles; Replica Directory Node
   single: Replica Directory Node

UCS system in the role Replica Directory Node have a complete read-only copy of
the domain database. Administrators cannot promote Replicate Directory Nodes to
the Primary Directory Node role.

A Replica Directory Node allows selective replication, a form of data
synchronization that only replicates a subset of the domain database. Selective
replication in UCS helps with data minimization, domain protection and
permission enforcement.

For example, imagine an organization with office locations in Berlin and Bremen.
Each location has a Replica Directory Node as domain controller. The Replica
Directory Nodes only replicate domain objects like users, groups and printers
that are relevant for their respective location. They don't store objects
assigned to other locations.

Replicate Directory Nodes are ideally suited as dedicated systems for load
intensive services with permanent read operations to the domain database because
the read operations run locally instead of across the computer network.

Managed Node
------------

.. index::
   single: domain roles; Managed Node
   single: Managed Node

UCS systems in the role Managed Node don't have any copy of the domain database.
Services on Managed Nodes read domain information over the network from one of
the other domain controller roles.

Clients
-------

Clients are systems in a domain that don't have a domain related role. In most
cases they consume services offered by the domain or other systems.

UCS offers dedicated client roles for desktop systems like Ubuntu, Linux and
macOS. UCS manages IP addresses for systems like network printers and routers
with the *IP client* role.

For Microsoft Windows related systems UCS offers the roles *Domain Trust
Account*, *Windows Domaincontroller* and *Windows Workstation / Server*. For
more information about the differences of these roles see `UCS system roles in
the UCS manual <https://docs.software-univention.de/manual.html#systemrollen>`_.

.. TODO : Replace the reference with an intersphinx label reference, once the manual is available as Sphinx document.

.. _concept-role:

Role concept
============

Univention Corporate Server (UCS) uses a role concept to assign different roles
that comprise certain tasks to the systems in a domain.

Primary Directory Node
----------------------

.. index::
   single: domain roles; Primary Directory Node
   single: Primary Directory Node

A UCS system with Primary Directory Node role is the first, the primary, domain
node in a domain. It is the only system with write permissions to the central
domain database and performs all write requests regarding data for the domain
database. Only one system in the domain can have the Primary Directory Node
role.

Backup Directory Node
---------------------

.. index::
   single: domain roles; Backup Directory Node
   single: Backup Directory Node

A UCS system with the Backup Directory Node role has a complete read-only copy
of the domain database, including security certificates. More than one UCS
system can have the Backup Directory Node role. In case the Primary Directory
Node is unavailable, recovery is impossible or needs too much time, an
administrator can promote a UCS system in the role Backup Directory Node to a
Primary Directory Node. The promotion cannot be reversed. For details on the
promotion process, see :ref:`uv-manual:domain-backup2master`.

Replica Directory Node
----------------------

.. index::
   single: domain roles; Replica Directory Node
   single: Replica Directory Node

UCS systems with the Replica Directory Node role have a complete read-only copy
of the domain database. Administrators cannot promote Replicate Directory Nodes
to the Primary Directory Node role or any other role unlike the Backup Directory
Node.

A Replica Directory Node optionally allows selective replication, a form of data
synchronization that replicates only a subset of the domain database. Selective
replication in UCS helps with data minimization, domain protection and
permission enforcement.

For example, imagine an organization with office locations in cities like Berlin
and Bremen. Each location has a Replica Directory Node as domain node. The
Replica Directory Nodes only replicate domain objects like users, groups and
printers that are relevant for their respective location. They don't store
objects assigned to other locations.

Replica Directory Nodes are ideally suited as dedicated systems for load
intensive services with permanent read operations to the domain database because
the read operations run locally instead of across the computer network.

Managed Node
------------

.. index::
   single: domain roles; Managed Node
   single: Managed Node

UCS systems with the Managed Node role don't have any copy of the domain database.
Services on Managed Nodes read domain information over the network from either
the Primary Directory Node or from one of the Backup Directory Nodes.

Clients
-------

Clients are systems in the domain's trust context. They don't have a special
role regarding domain services as the other roles described before. In most
cases they consume services offered by the domain or other systems.

UCS offers dedicated client roles for desktop systems like Ubuntu, other Linux
desktops and macOS. UCS manages IP addresses and DNS entries for systems like
network printers and routers with the *IP client* role.

For Microsoft Windows related systems, UCS offers the roles *Domain Trust
Account*, *Windows Domaincontroller* and *Windows Workstation / Server*. For
more information about the differences of these roles see
:ref:`uv-manual:system-roles`.

.. TODO : Replace the reference with an intersphinx label reference, once the manual is available as Sphinx document.

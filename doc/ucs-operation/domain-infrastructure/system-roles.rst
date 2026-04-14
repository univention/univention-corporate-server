.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-system-roles:

Understanding system roles
==========================

You can install systems in different *system roles* in a Nubus for UCS domain.
This page provides a characterization of the different roles.

.. seealso::

   For more information about the role concept in Nubus for UCS,
   see :external+uv-architecture:ref:`concept-role`
   in :cite:t:`ucs-architecture`.

.. _domain-infrastructure-system-roles-primary-directory-node:

Primary Directory Node
----------------------

A system with the Primary Directory Node role
is the primary domain controller of a Nubus for UCS domain.
It's always the first system installed in a Nubus for UCS domain.

The Primary Directory Node stores domain data,
such as users, groups, printers,
and the TLS security certificates.
Systems with the Backup Directory Node role automatically receive copies of this data.

.. important::

   The Primary Directory Node is critical to domain operations.
   To ensure continued service availability and eliminate single points of disruption,
   see :ref:`deployment-primary-dn-resilience` for strategies on redundancy and failover.

.. _domain-infrastructure-system-roles-backup-directory-node:

Backup Directory Node
---------------------

The Primary Directory Node stores a read-only copy of all the domain data and TLS security certificates.
It can't write changes to the domain data.

The Backup Directory Node is the fallback system for the Primary Directory Node.
If the Primary Directory Node fails,
a Backup Directory Node can adopt the role of the Primary Directory Node permanently.
For information about the backup to primary promotion,
see :ref:`deployment-primary-dn-resilience-backup-primary-promotion`.

.. _domain-infrastructure-system-roles-replica-directory-node:

Replica Directory Node
----------------------

Servers with the Replica Directory Node role have all the domain data saved as read-only copy.
In contrast to the Backup Directory Node, they don't have all security certificates.

Services running on a Replica Directory Node access LDAP directory data
through the local LDAP directory service.
Replica Directory Node systems are ideal for site servers and the distribution of high-load services.

A Replica Directory Node doesn't allow promotion to a Primary Directory Node.

.. _domain-infrastructure-system-roles-managed-node:

Managed Node
------------

Managed Nodes are Nubus for UCS systems without a local LDAP directory service.
They access domain data through other servers in the domain.
They're suitable for services that don't require a local database for authentication.

.. _domain-infrastructure-system-roles-ubuntu:

Ubuntu
------

You can manage Ubuntu clients in Nubus with the *Ubuntu* system role.
For more information, see
:external+uv-ucs-manual:ref:`computers-ubuntu`
in :cite:t:`ucs-manual`.

.. _domain-infrastructure-system-roles-linux:

Linux
-----

You manage other Linux systems that neither match Nubus for UCS nor Ubuntu
with the *Linux* system role,
for example, Debian GNU/Linux or CentOS.
For information about the integration,
see :cite:t:`ext-doc-domain`.

.. _domain-infrastructure-system-roles-macos:

macOS
-----

You can join macOS systems into a Nubus for UCS domain through Samba.
For information about the integration,
see :ref:`domain-infrastructure-join-macos`.

.. _domain-infrastructure-system-roles-domain-trust-account:

Domain Trust Account
--------------------

Nubus uses the *Domain Trust Account* system role
for trust relationships between Windows Active Directory domains and Nubus for UCS domains.

.. _domain-infrastructure-system-roles-windows-domain-controller:

Windows Domaincontroller
------------------------

Windows domain controllers in a Samba environment use the *Windows Domaincontroller* system role.

.. _domain-infrastructure-system-roles-windows-workstation-server:

Windows Workstation and Windows Server
--------------------------------------

Windows clients and Windows Managed Nodes
use the *Windows Workstation* or *Windows Server* system role.

.. _domain-infrastructure-system-roles-ip-managed-client:

IP client
---------

The IP client system role allows the integration of systems
not listed in :ref:`domain-infrastructure-system-roles`
into the IP management of Nubus for DNS and DHCP,
such as network printers or routers.

.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure:

*********************
Domain infrastructure
*********************

This chapter covers the infrastructure foundation of a Nubus for UCS domain.
A Nubus for UCS domain relies on multiple systems with different roles and responsibilities
that work together to provide directory, authentication, and management services.

The Primary Directory Node serves as the central hub of your domain,
storing and managing all domain data.
To keep your domain available and resilient,
you need to understand both the system roles you can deploy
and the strategies for protecting against single points of disruption.

System roles
   Understand the system roles you can deploy in a Nubus for UCS domain,
   from the Primary Directory Node that stores all domain data
   to Backup, Replica, and Managed Nodes.
   See :ref:`domain-infrastructure-system-roles`.

Domain join
   Enable systems to join your Nubus for UCS domain.
   Learn how UCS, Windows, Ubuntu, and macOS systems join the domain,
   configure domain join through the command line or management module,
   and manage join scripts for automated system configuration.
   See :ref:`domain-infrastructure-join`.

Certificate management
   Understand how UCS manages TLS certificates,
   the built-in CA on the Primary Directory Node,
   certificate validity monitoring, and renewal procedures.
   See :ref:`domain-infrastructure-tls`.

Kerberos authentication
   Learn how Nubus for UCS uses Kerberos for domain authentication,
   how the system selects the Key Distribution Center,
   and how to configure the Kerberos administration server.
   See :ref:`domain-infrastructure-kerberos`.

Redundancy and failover for the Primary Directory Node
   Protect your domain against disruption to the Primary Directory Node
   by distributing directory data across Backup and Replica Directory Nodes
   and by promoting a Backup Directory Node to Primary when needed.
   See :ref:`deployment-primary-dn-resilience`.

Domain activity logging
   Record and monitor important domain events including user and object management,
   app installations and updates, server password changes, domain joins,
   and system updates using the :program:`Admin Diary` app.
   See :ref:`domain-activity-logging`.

.. toctree::
   :caption: Contents

   system-roles
   domain-join
   tls
   kerberos
   ha
   activity-logging

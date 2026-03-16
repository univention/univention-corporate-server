.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _doc-entry:
.. _intro:

************
Introduction
************

.. TODO: Update this paragraph when new chapters or topics are added to the manual.

Welcome to the Operation Manual for Nubus for Univention Corporate Server (UCS).

This manual targets technical administrators who operate UCS domains and systems.
It assumes familiarity with Linux system administration,
networking concepts,
and directory services such as LDAP.

This manual covers the following topics:
domain infrastructure, management interfaces, software lifecycle,
identity and access management, and system administration.
Each chapter includes conceptual overviews and task-oriented procedures.

For installation procedures,
see the :ref:`deployment` chapter.
For architectural concepts and design decisions,
see :cite:t:`ucs-architecture`.

.. _intro-understanding-nubus-for-ucs:

Understanding Nubus and UCS
============================

This section explains what Nubus and UCS are, how they relate to each other,
and what capabilities they provide when deployed together.

.. _intro-understanding-nubus-for-ucs-whats-nubus:

What is Nubus?
--------------

Univention Nubus is an open-source solution for identity and access management.
It provides a portal as the central entry point for end users
and provides the following core capabilities:

* Administration of users and groups across your organization.

* User self-service capabilities through the portal.

* Integration interfaces that connect various applications to the identity system.

* Single sign-on across integrated applications.

Nubus consolidates identity management and application access into one system.
Built-in integrations connect third-party applications to the identity management system,
eliminating the need for separate authentication systems.

Nubus runs on different platforms.
This manual covers Nubus for Univention Corporate Server.
For Nubus on Kubernetes, see
:cite:t:`uv-nubus-kubernetes-operation`.

.. _intro-understanding-nubus-for-ucs-whats-ucs:

What is UCS?
------------

Univention Corporate Server (UCS) is a Linux-based server operating system
that serves as the platform for deploying Nubus.
UCS provides the infrastructure layer on which Nubus runs.

Nubus for UCS deployment provides two layers of functionality.
Nubus covers the core identity and access management capabilities,
and UCS adds the broader infrastructure services:

* Network services for DHCP and DNS administration.
* File and print services.
* Computer administration and monitoring.
* Mail services.
* The Univention App Center for installing additional applications and extensions.
* Services for integrating or replacing existing Microsoft Active Directory domains.

.. _intro-understanding-nubus-for-ucs-together:

How Nubus and UCS work together
--------------------------------

Nubus for UCS uses a unified administration model.
All components operate in a shared security and trust context—the Nubus for UCS domain.
UCS combines Nubus and the infrastructure services through the *Management UI*,
a unified web interface for managing the system
across distributed and virtualized environments.

Nubus for UCS includes extensive interfaces to infrastructure components
and management tools from third-party vendors,
so you can integrate it with existing environments.

You can find details on each of these components throughout this manual.

.. _intro-key-concepts:

Key concepts
============

The following concepts are central to how Nubus for UCS operates.
Each section provides a brief overview.
For detailed information, see the referenced chapters.

.. _intro-domain-concept:

Domain concept
--------------

Nubus for UCS manages your IT infrastructure within a common security and trust context
called the Nubus for UCS domain.
The domain contains all servers, clients, and users.
During installation,
you assign each Nubus for UCS system a server role.
:numref:`intro-domain-concept-figure` illustrates a domain concept across multiple locations
with different system roles.

For detailed information on system roles,
domain join procedures,
and client integration,
see :ref:`domain-infrastructure`.

.. _intro-domain-concept-figure:

.. figure:: /images/domainconcept.*
   :alt: Nubus for UCS domain concept

   Nubus for UCS domain concept

.. _intro-management-ui:

Management UI
-------------

The *Management UI* provides web-based access to the LDAP directory
through management modules.
You can use management modules to display, edit, delete,
and search data in the LDAP directory.
The web interface provides wizards for administering users, groups, networks,
computers, directory shares, and printers.
For an overview of the available modules,
see :numref:`intro-management-ui-figure`.

.. _intro-management-ui-figure:

.. figure:: /images/umc-favorites-tab.*
   :alt: Management modules in the Management UI

   Management modules in the *Management UI*

For command-line administration,
:term:`Univention Directory Manager` lets you perform
domain-wide administrative tasks through scripts or automated processes.
Management modules also let you configure individual computers,
including software installation and service monitoring.

.. TODO: Add cross-reference after Management UI and UDM content is available in the document. See univention/dev/ucs#2591.

For detailed information about the Management UI and UDM commands,
see :external+uv-ucs-manual:ref:`central-general`
in :cite:t:`ucs-manual`.

.. _intro-ldap-directory-service:

LDAP directory service
----------------------

An LDAP directory stores the data you need across the domain,
including user accounts and service configurations such as DHCP.
Central data management in the LDAP directory eliminates duplicate data entry
and reduces errors and inconsistencies.

.. TODO: Replace this cross-reference after LDAP directory content is available in the document. See univention/dev/ucs#3326.

For detailed information about LDAP schema management,
replication topology,
and directory node roles,
see :external+uv-ucs-manual:ref:`domain-ldap`
in :cite:t:`ucs-manual`.

.. _intro-policy-concept:

Policy concept
--------------

LDAP directories have a hierarchical structure.
Objects such as users and computers exist in containers,
and containers can contain other containers.
The root container forms the LDAP base object.

Policies describe settings that apply to multiple objects.
When you link policies to containers,
they apply to all objects in that container and its subcontainers,
without requiring you to configure each object individually.

Nubus for UCS uses policies for various administrative tasks,
including:

* Maintenance policies that control when systems install or remove packages,
  see :ref:`lifecycle-package-maintenance-policy`.

* Password policies that enforce security requirements for user accounts,
  see :ref:`password-management-policies`.

* Repository server policies that specify which update server the systems use,
  see :ref:`lifecycle-local-repository-policy`.

For information about creating and managing policies,
see :external+uv-nubus-manual:ref:`nubus-domain-policies`
in :cite:t:`uv-nubus-manual`.

.. _intro-app-center:

Univention App Center
---------------------

The Univention App Center adds applications and integrations to Nubus for UCS.
Most applications integrate directly into the *Management UI* as management modules,
so you can manage application data at the domain level.

The :ref:`lifecycle` chapter covers App Center installation and management in detail.

.. _intro-listener-notifier-replication:

Listener/notifier replication
------------------------------

The listener/notifier mechanism propagates changes across the domain.
When you create, edit, or delete entries in the LDAP directory,
the mechanism triggers defined actions on the affected computers.
For example,
when you create a directory share,
the mechanism updates the NFS and Samba configuration files
and creates the directory on the selected server.

You can extend the listener/notifier mechanism with custom modules
to integrate third-party products with the LDAP directory service.

.. TODO: Replace this cross-reference after Listener/Notifier content is available in the document. See univention/dev/ucs#3327.

For detailed information about the listener/notifier mechanism,
see :external+uv-ucs-manual:ref:`domain-listener-notifier`
in :cite:t:`ucs-manual`.

.. _feedback:

Feedback
========

Your feedback on this documentation is welcome.
If you have any comments, suggestions, or corrections,
`submit your feedback <https://www.univention.com/feedback/?ucs-operation-manual=generic>`_
to improve the document.

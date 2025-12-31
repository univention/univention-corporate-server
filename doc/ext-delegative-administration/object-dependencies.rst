.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-object-dependencies:

*******************
Object dependencies
*******************

This section documents the dependencies between UDM objects and the minimal permissions required
to make these relationships functional.
Understanding these dependencies is crucial when creating or modifying UDM roles,
where object permissions alone are insufficient unless related object types are also accessible.

This section is for administrators who want to create their own roles.
You need to know the concept for delegative administration
and the Univention Directory Manager (UDM):

* :ref:`da-concepts`
* :external+uv-ucs-architecture:ref:`services-udm` in :cite:t:`ucs-architecture`

This section provides the following information:

* :ref:`da-object-dependencies-reference-map`:
  A comprehensive table mapping UDM object types to their dependencies and required permissions.

* :ref:`da-object-dependencies-permissions-by-type`:
  Permission requirements organized by operation type, such as create, modify, and search.

* :ref:`da-object-dependencies-examples`:
  Examples showing how dependencies affect existing UDM roles
  like domain administrator, organizational unit administrator,
  helpdesk operator, Linux OU client manager, and Self Service profile.

.. important::

   When creating or modifying roles,
   it happens to overlook object permissions.
   For example, for computer objects,
   these permissions are insufficient
   unless related object types are also accessible, such as network objects or DNS objects.
   Documentation often doesn't cover these dependencies explicitly.
   This can lead to roles appearing correct,
   but being incomplete or functionally limited.

UDM objects can have several references to other UDM objects.
When you design policies,
you need to ensure that Nubus can resolve these references to create or modify objects.
For example, when you create a user object, they must have a primary group.
To create a user object, the actor needs access to at last some user group objects
for being able to assign them as primary group.
Another example are computer objects.
Creating computer objects requires access to related objects such as DNS or DHCP objects.

.. _da-object-dependencies-reference-map:

Object reference map
====================

:numref:`da-object-dependencies-reference-map-table`
lists all UDM object types
that hold references to other object types.
They all require ``read`` permission
on the referenced objects to make the relations usable.
While most object references require **read** permission on the referenced object,
some specific use cases, such as updating relationship, may require **modify** permission.

.. _da-object-dependencies-reference-map-table:

.. list-table:: Object reference map for ``read`` permissions
   :header-rows: 1
   :widths: 2 2 7

   * - Primary object
     - Refers to
     - Description

   * - ``computers/*``
     - ``networks/network``
     - To select a network during create and modify.

   * - ``computers/*``
     - ``dns/*``
     - DNS configuration for clients.

   * - ``computers/*``
     - ``dhcp/*``
     - DHCP configuration for clients.

   * - ``computers/*``
     - ``policies/*``
     - Policy application overview.

   * - ``container/cn``
     - ``policies/*``
     - Policy application to containers.

   * - ``container/ou``
     - ``policies/*``
     - Policy application to organizational units.

   * - ``groups/group``
     - ``users/user``
     - Required for managing group memberships.

   * - ``groups/group``
     - ``computers/*``
     - Required for managing group memberships.

   * - ``groups/group``
     - ``groups/group``
     - Group hierarchy management including nested groups.

   * - ``groups/group``
     - ``policies/*``
     - Policy application to groups.

   * - ``mail/folder``
     - ``mail/domain``
     - Mail folder domain association.

   * - ``nagios/service``
     - ``computers/*``
     - Monitoring service targets.

   * - ``shares/printer``
     - ``computers/*``
     - Printer host connection.

   * - ``shares/share``
     - ``computers/*``
     - Share location and access.

   * - ``users/user``
     - ``groups/group``
     - To assign user to groups and for primary group assignment.

   * - ``users/user``
     - ``mail/domain``
     - Email domain assignment and configuration.

   * - ``users/user``
     - ``users/user``
     - Secretary and delegation relationships.

   * - ``users/user``
     - ``policies/*``
     - Policy application to users.

.. _da-object-dependencies-permissions-by-type:

Permission requirements by operation type
=========================================

This section lists the permission requirements grouped by operation type.
It covers the operations *read*, *create*, *modify*, and *search*.
Keep the following definitions for the terms used in this section in mind:

Primary object type
   Refers to the object that the actor wants to change, for example a user object.

Referenced object type
   Refers to all objects that the primary object has references to.
   To access referenced objects, the actor needs at least read operation.

Container object type
   Is a container in the LDAP directory,
   such as a container (``cn``), or organizational unit (``ou``).

For a list of available permissions,
see :ref:`da-concepts-role-definition-grant-properties-permission`.

Create
   For creating objects, you typically need the following permissions:

   * ``write`` permission on the primary object type.
   * ``read`` permission on all referenced object types.
   * ``read`` permission on container objects in a container.

Modify
   For modifying objects, you typically need the following permissions:

   * ``modify`` permission on the primary object.
   * ``read`` permission on the referenced objects.

Search
   For searching objects, you typically need the following permissions:

   * ``read`` permission on the primary object type.
   * ``read`` permission on referenced objects for display purposes.
   * ``search`` permission—optionally—on referenced object types for proper filtering.

.. _da-object-dependencies-examples:

Examples: Current UDM roles and their dependencies
==================================================

The following examples illustrate how object dependencies affect the default UDM roles defined in the system.

For a list of defined roles for delegative administration,
see :ref:`da-roles`.

.. _da-object-dependencies-examples-domain-admin:

*Domain Administrator* role
---------------------------

The :ref:`da-roles-domain-administrator` role has access to all objects and properties, so it doesn't face dependency issues.

.. _da-object-dependencies-examples-ou-admin:

*Organizational Unit Admin* role
--------------------------------

The :ref:`da-roles-organization-unit-admin` role manages users and groups within specific organizational units (OUs).

Key dependencies for this role:
   * *Users* require access to *user groups* for group assignments.

   * *Users* require access to ``mail/domain`` objects for email configuration.

   * *Users* and *user groups* require access to *policies* for policy enforcement.

   * *Container* access allows for organizational structure navigation.

Without proper dependency permissions:

* User group assignments would fail.
* Email domain selection would be unavailable.
* Policy enforcement wouldn't work.
* The OU structure limits navigation.

.. _da-object-dependencies-examples-helpdesk-operator:

*Helpdesk Operator* role
------------------------

The :ref:`da-roles-helpdesk-operator` role focuses on password management and basic user support.

Key dependencies for this role:
   * *Users* require access to *user groups* for context and verification.
   * *Container* access allows for organizational structure navigation.

.. _da-object-dependencies-examples-linux-ou-client-manager:

*Linux OU Client Manager* role
------------------------------

The :ref:`da-roles-linux-ou-client-manager` role manages Linux computers and related infrastructure.

Key dependencies for this role:
   * *Computers* require access to *networks* for network selection.

   * *Computers* require access to *DNS records* for name resolution.
     The allowed DNS and DHCP records are the following:

     * *DNS Host*
     * *DNS Pointer*
     * *DHCP Service*
     * *DHCP Subnet*
     * Network objects
     * Containers for Network, DHCP, and DNS

   * *Computers* require access to *DHCP services* for IP configuration.

   * *Computers* require access to *groups* for computer group memberships.

   * *Container* access allows for organizational structure navigation.

Without these dependency permissions:

* Network drop-downs would be empty.
* DNS configuration options wouldn't be available.
* Computer group assignments would fail.
* Placement in organizational units might not work properly.

.. _da-object-dependencies-examples-self-service-profile:

*Self-Service Profile* role
---------------------------

The ``udm:default-roles:self-service-profile`` role allows users to modify their own profile information.

Key dependencies for this role:
   * Primarily operates on the user's own object using the ``is-self`` condition.
   * Minimal external dependencies due to restricted scope.

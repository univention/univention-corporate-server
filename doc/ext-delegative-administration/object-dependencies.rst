.. SPDX-FileCopyrightText: 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-object-dependencies:

*******************
Object Dependencies
*******************

This section documents the dependencies between UDM objects and the minimal permissions required to make these relationships functional.
Understanding these dependencies is crucial when creating or modifying UDM roles, where object permissions alone are insufficient unless related object types are also accessible.

.. note::

   When defining new roles or modifying existing ones, it's easy to overlook that object permissions on their own (e.g., for computer objects) are insufficient unless related object types (like network, DNS, etc.) are also accessible.
   These dependencies are often not explicitly documented, which leads to roles being incomplete or functionally limited despite appearing correct.

Object reference patterns
=========================

UDM uses several mechanisms to establish references between objects:

#. **Direct DN References**: Properties that store DNs of other objects (e.g., ``primaryGroup``, ``groups``)
#. **Syntax-Based References**: Properties using UDM syntax classes like ``GroupDN``, ``UserDN``, ``UDM_Objects``
#. **Service Dependencies**: Objects that require access to related service objects (DNS, DHCP, etc.)

Object reference map
====================

The following table lists all UDM object types that hold references to other object types, along with the minimal permissions required on the referenced objects to make the relations usable.

.. note::

   While most object references require **read** permission on the referenced object, some specific use cases may require additional permissions:

   - **search** permission may be needed for drop-down or selection widgets
   - **modify** permission may be required when the relationship itself needs to be changed
   - Context-specific permissions may apply based on the role and operation being performed

.. list-table:: Object Reference Map
   :header-rows: 1
   :widths: 20 20 15 45

   * - Primary Object
     - Refers To
     - Required Permission
     - Description
   * - ``users/user``
     - ``groups/group``
     - read
     - To assign user to groups and for primary group assignment
   * - ``users/user``
     - ``mail/domain``
     - read
     - Email domain assignment and configuration
   * - ``users/user``
     - ``users/user``
     - read
     - Secretary and delegation relationships
   * - ``users/user``
     - ``policies/*``
     - read
     - Policy application to users
   * - ``groups/group``
     - ``users/user``
     - read
     - Required for managing group memberships
   * - ``groups/group``
     - ``computers/*``
     - read
     - Required for managing group memberships
   * - ``groups/group``
     - ``groups/group``
     - read
     - Group hierarchy management (nested groups)
   * - ``groups/group``
     - ``policies/*``
     - read
     - Policy application to groups
   * - ``computers/*``
     - ``networks/network``
     - read
     - Needed to select a network during creation/modification
   * - ``computers/*``
     - ``dns/*``
     - read
     - DNS configuration for clients
   * - ``computers/*``
     - ``dhcp/*``
     - read
     - DHCP configuration for clients
   * - ``computers/*``
     - ``policies/*``
     - read
     - Policy application overview
   * - ``shares/share``
     - ``computers/*``
     - read
     - Share location and access
   * - ``nagios/service``
     - ``computers/*``
     - read
     - Monitoring service targets
   * - ``mail/folder``
     - ``mail/domain``
     - read
     - Mail folder domain association
   * - ``shares/printer``
     - ``computers/*``
     - read
     - Printer host connection
   * - ``container/ou``
     - ``policies/*``
     - read
     - Policy application to organizational units
   * - ``container/cn``
     - ``policies/*``
     - read
     - Policy application to organizational units


Permission requirements by operation type
=========================================

Create operations
-----------------

When creating objects, the following permissions are typically required:

- **Write** permission on the primary object type
- **Read** permission on all referenced object types
- **Search** permission on referenced object types (for drop-down population)
- **Read** permission on container objects in the target location

Modify operations
-----------------

When modifying objects that change references:

- **Modify** permission on the primary object
- **Read** permission on newly referenced objects
- **Search** permission for drop-down/selection widgets

Search operations
-----------------

When searching and displaying objects:

- **Search** permission on the primary object type
- **Read** permission on referenced objects (for display purposes)
- May require **search** permission on referenced types for proper filtering

Examples: Current UDM roles and their dependencies
==================================================

The following examples illustrate how object dependencies affect the default UDM roles defined in the system.

Domain Administrator role
-------------------------

The ``udm:default-roles:domain-administrator`` role has access to all objects and properties, so it doesn't face dependency issues.

Organizational Unit Admin role
------------------------------

The ``udm:default-roles:organizational-unit-admin`` role manages users and groups within specific OUs.

**Key dependencies for this role:**

- **Users** require access to **groups** for group assignments
- **Users** require access to **mail/domain** for email configuration
- **Users** and **groups** require access to **policies** for policy application
- **Container** access is needed for organizational structure navigation

Without proper dependency permissions:

- User group assignments would fail
- Email domain selection would be unavailable
- Policy application would not work
- Navigation within the OU structure would be limited

Helpdesk Operator role
----------------------

The ``udm:default-roles:helpdesk-operator`` role focuses on password management and basic user support.

**Key dependencies for this role:**

- **Users** require access to **groups** for context and verification
- **Container** access is needed for OU navigation

Linux OU Client Manager role
----------------------------

The ``udm:default-roles:linux-ou-client-manager`` role manages Linux computers and related infrastructure.

**Key dependencies for this role:**

- **Computers** require access to **networks** for network selection
- **Computers** require access to **DNS records** for name resolution
- **Computers** require access to **DHCP services** for IP configuration
- **Computers** require access to **groups** for computer group memberships
- **Container** access is needed for placement in organizational structure

Without these dependency permissions:

- Network drop-downs would be empty
- DNS configuration options would not be available
- Computer group assignments would fail
- Placement in organizational units might not work properly

Self-Service Profile role
-------------------------

The ``udm:default-roles:self-service-profile`` role allows users to modify their own profile information.

**Key dependencies for this role:**

- Primarily operates on the user's own object (using ``is-self`` condition)
- Minimal external dependencies due to restricted scope

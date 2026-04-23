.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-delegated-administration:

Delegated administration for management modules
===============================================

By default, only members of the ``Domain Admins`` group can access all management modules.
With a *UMC policy*, you can grant specific groups or individual users access to selected modules.
This lets you delegate access without giving them full domain administration rights.
For example, you can allow a helpdesk team to manage printers without letting them access user or group administration.

.. _management-interface-delegated-administration-how-it-works:

How delegated administration works
-----------------------------------

A *UMC policy* defines a list of *UMC operation sets*.
Each operation set covers one or more management modules and the actions you can perform in them.
When you assign a *UMC policy* to a group or user,
that group or user can see and use the modules the policy covers in the *Management UI*.

Policies combine.
A user gains access from every *UMC* policy assigned to them directly,
plus any policies assigned to the groups they belong to.
For more information about how policies work in general,
see :external+uv-nubus-manual:ref:`nubus-domain-policies`
in :cite:t:`uv-nubus-manual`.

.. caution::

   The system only evaluates *UMC policies* assigned directly to
   user accounts, computer accounts, and groups.
   Nubus doesn't evaluate nested group memberships—groups that belong to other groups.

.. _management-interface-delegated-administration-operation-sets:

Built-in UMC operation sets
----------------------------

:numref:`management-interface-delegated-administration-operation-sets-table` describes the built-in operation sets for *UMC policies*.
Use these when you create a *UMC policy*.

.. _management-interface-delegated-administration-operation-sets-table:

.. list-table:: Built-in UMC operation sets
   :header-rows: 1
   :widths: 2 3 7

   * - Operation set name
     - Module shown in the *Management UI*
     - Description

   * - ``udm-all``
     - All management modules
     - Grants access to all management modules.

   * - ``udm-users``
     - *Users*
     - Grants access to the *Users* management module.

   * - ``udm-groups``
     - *Groups*
     - Grants access to the *Groups* management module.

   * - ``udm-computers``
     - *Computers*
     - Grants access to the *Computers* management module.

   * - ``udm-printers``
     - *Print shares*
     - Grants access to the *Print shares* management module.

   * - ``udm-shares``
     - *Shares*
     - Grants access to the *Shares* management module.

   * - ``udm-policies``
     - *Policies*
     - Grants access to the *Policies* management module.

   * - ``udm-mail``
     - *Mail*
     - Grants access to the *Mail* management module.

   * - ``udm-network``
     - *Networks*
     - Grants access to the *Networks* management module.

   * - ``udm-dns``
     - *DNS*
     - Grants access to the *DNS* management module.

   * - ``udm-dhcp``
     - *DHCP*
     - Grants access to the *DHCP* management module.

   * - ``udm-nagios``
     - *Nagios*
     - Grants access to the *Nagios* management module for configuring NRPE host monitoring.
       Nagios server management isn't available since UCS 5.2.

   * - ``udm-navigation``
     - *LDAP directory*
     - Grants access to the *LDAP directory browser*.

   * - ``udm-reports``
     - —
     - Grants the ability to create directory reports.
       Reports are available in the *Users*, *Groups*, and *Computers* modules
       under :menuselection:`More --> Create report`.

.. _management-interface-delegated-administration-ldap:

LDAP access rights
------------------

A *UMC policy* controls which modules a user can see and open.
For modules that read or write data in the LDAP directory,
such as *Users*, *Groups*, or *Print shares*,
the user also needs sufficient LDAP access rights.

By default, only members of ``Domain Admins`` and certain system accounts
have write access to the LDAP directory.
If a user can open a module through a *UMC policy*
but doesn't have the necessary LDAP access rights,
the module displays a *Permission denied* error and blocks the changes.

.. TODO: Update cross-reference here after LDAP access control section has been migrated to UCS Operation Manual

For information about configuring LDAP access rights,
see :external+uv-ucs-manual:ref:`domain-ldap-acls`
in :cite:t:`ucs-manual`.

.. _management-interface-delegated-administration-configure:

Group access to management modules
----------------------------------

The following steps show how to create a *UMC policy*,
assign it the operation sets you want,
and link it to a group.
The example uses the *Print shares* module and a helpdesk group.

.. _management-interface-delegated-administration-configure-prerequisites:

Prerequisites
~~~~~~~~~~~~~

Before you begin, verify the following conditions:

* Sign in as a member of ``Domain Admins``.

* The target group must already exist.
  If not, create it in :menuselection:`Users --> Groups` first.

* For modules that write to the LDAP directory,
  the group needs sufficient LDAP access rights.
  See :ref:`management-interface-delegated-administration-ldap`.

.. _management-interface-delegated-administration-configure-create-policy:

Create a UMC policy
~~~~~~~~~~~~~~~~~~~

Follow these steps to create a *UMC policy*:

#. Navigate to :menuselection:`Domain --> Policies`.

#. Click :guilabel:`Add`.

#. Select :guilabel:`UMC` as the policy type.

#. Choose a container to store the policy in.

#. Enter a name for the policy,
   for example ``helpdesk-printers``.

#. In the :guilabel:`List of allowed UMC operation sets` field,
   select the operation sets you want to grant.
   For printer administration,
   select ``udm-printers``.

#. Click :guilabel:`Save`.

.. _management-interface-delegated-administration-configure-assign-policy:

Assign the policy to a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow these steps to assign the *UMC policy*:

#. Navigate to :menuselection:`Users --> Groups`.

#. Select the group,
   for example ``Helpdesk``.

#. Go to the :guilabel:`Policies` tab.

#. In the :guilabel:`UMC` section,
   select the policy you created,
   for example ``helpdesk-printers``.

#. Click :guilabel:`Save`.

Members of the group can now see the *Print shares* module
when they sign in to the *Management UI*.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-policies`
      in :cite:t:`uv-nubus-manual`
      for information about how policies work and how to manage them.

   :external+uv-ucs-manual:ref:`domain-ldap-acls`
      in :cite:t:`ucs-manual`
      for information about LDAP access control lists.

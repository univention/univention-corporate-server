.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-package-maintenance-policy:

Package maintenance policy
==========================

This section describes how you can use a package maintenance policy
to control when Nubus for UCS installs or removes packages.
For information about package management,
see :ref:`lifecycle-package-installation-management`.
For information about policies in general,
see :external+uv-nubus-manual:ref:`nubus-domain-policies`
in :cite:t:`uv-nubus-manual`.

A *Maintenance Policy* defines when
Nubus for UCS runs automatic updates or maintenance tasks.
You can schedule the maintenance for a specific time or
trigger it based on system events, such as after boot or before shutdown.
For example:

* Check for available release updates and install them.
  For more information, see :ref:`lifecycle-update-strategies-methods-policy`.

* Install or remove packages with package lists.
  For more information, see :ref:`lifecycle-package-installation-management-policy`.

* Install available errata updates.

.. seealso::

   :ref:`lifecycle-package-installation-management`
      for information about package management.

   :external+uv-nubus-manual:ref:`nubus-domain-policies`
      in :cite:t:`uv-nubus-manual`
      for information about policies in general.

.. _lifecycle-package-maintenance-policy-create:

How to create a maintenance policy
----------------------------------

You can create a maintenance policy in two ways.
Both ways result in the same policy behavior.
Use the first way for multi-system environments,
and the second way for system-specific configurations.

Centralized policy management:
   Create a policy once and assign it to multiple systems.

Computer object policies:
   Assign policies directly to individual computer objects.

.. _lifecycle-package-maintenance-policy-create-centralized:

Centralized policy management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a maintenance policy, use the following steps:

#. Open the :external+uv-nubus-manual:ref:`nubus-domain-policies`.

#. To create a policy, click :guilabel:`Add`.

#. Select ``Policy: Maintenance`` for the *Type*
   and choose a *Container* for the location in the directory service.
   Click :guilabel:`Next`.

#. Define the maintenance settings.
   For an explanation of the fields,
   see :ref:`lifecycle-package-maintenance-policy-fields`.

#. To save the policy, click :guilabel:`Save`.

.. _lifecycle-package-maintenance-policy-create-computer-object:

Computer object policies
~~~~~~~~~~~~~~~~~~~~~~~~

You can also create a *Maintenance Policy* directly at the computer object
in the *Computers* management module.
Use the following steps:

#. Open the :external+uv-nubus-manual:ref:`nubus-computer-management`.

#. Navigate to the *Policies* tab and select the section *Policy: Maintenance*.

#. Select an existing policy configuration or click :guilabel:`Create new Policy`.

#. Define the maintenance settings.
   For an explanation of the fields,
   see :ref:`lifecycle-package-maintenance-policy-fields`.

#. To save the maintenance settings, click :guilabel:`Save`.

.. _lifecycle-package-maintenance-policy-fields:

Understanding maintenance policy fields
---------------------------------------

You can configure the following settings in the *Maintenance Policy*:

.. _lifecycle-package-maintenance-policy-startup:

Perform maintenance after system startup
   If you activate this option,
   the system performs the configured updates when you start the computer.

.. _lifecycle-package-maintenance-policy-shutdown:

Perform maintenance before system shutdown
   If you activate this option,
   the system performs the configured updates when you shut down the computer.

.. _lifecycle-package-maintenance-policy-cron:

Use Cron settings
   If you activate this option,
   use the *Month*, *Day of week*, *Day*, *Hour*, and *Minute* fields
   to specify when the configured updates run.

.. _lifecycle-package-maintenance-policy-reboot:

Reboot after maintenance
   This option triggers an automatic restart after release updates
   either immediately or after a specified number of hours.

.. _lifecycle-package-maintenance-policy-related:

Related policies
----------------

The *Maintenance Policy* coordinates with other policies:

* Control how and when you install release updates, see :ref:`lifecycle-update-strategies-methods-policy`.
* Manage package installation and removal, see :ref:`lifecycle-package-installation-management-policy`.

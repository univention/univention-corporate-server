.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle:

*********
Lifecycle
*********

Software lifecycle management in Nubus for UCS involves
understanding versioning, planning and performing updates,
managing repositories, installing additional software,
and monitoring what's installed across your domain.
This chapter covers the following workflows:

System updates and maintenance
   Keep your systems current with security fixes, bug fixes, and features.
   Start with :ref:`lifecycle-versioning` to understand release types,
   then review :ref:`lifecycle-update-strategies` for planning multi-server updates.
   For technical details about the update process,
   see :ref:`lifecycle-perform-updates`.

Package management
   Install, remove, and manage software packages on your systems.
   For routine package operations,
   see :ref:`lifecycle-package-installation-management`.
   To automate package installation and removal on a schedule or system event,
   see :ref:`lifecycle-package-maintenance-policy`.

Software distribution
   Control how Nubus for UCS systems obtain and install software.
   For multi-system environments or offline scenarios,
   set up local repositories—
   see :ref:`lifecycle-local-repository-servers`.

Application management
   Extend your domain with additional applications from Univention App Center.
   The App Center handles the complete application lifecycle,
   from installation and configuration to updates and removal.
   See :ref:`lifecycle-app-center`.

Domain-wide software monitoring
   Track which package versions all systems have installed in your domain.
   The software monitor helps you identify problems and plan staged updates.
   See :ref:`lifecycle-software-monitor`.

.. toctree::

   versioning
   update-strategies
   perform-updates
   package-installation-management
   package-maintenance-policy
   local-repository-servers
   app-center
   software-monitor

.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle:

*********
Lifecycle
*********

Software lifecycle management in Nubus for UCS involves
understanding versioning, planning updates, performing updates,
managing repositories, and installing additional software.
This chapter covers the following workflows:

System updates and maintenance
   Keep your systems current with security fixes, bug fixes, and new features.
   Start with :ref:`lifecycle-versioning` to understand release types,
   then review :ref:`lifecycle-update-strategies` for planning multi-server updates.
   For technical details about the update process,
   see :ref:`lifecycle-perform-updates`.

Software distribution and package management
   Control how Nubus for UCS systems obtain and install software.
   For multi-system environments or offline scenarios,
   set up local repositories—
   see :ref:`lifecycle-local-repository-servers`.
   For routine package operations,
   see :ref:`lifecycle-package-installation-management`.

.. toctree::

   versioning
   update-strategies
   perform-updates
   package-installation-management
   package-maintenance-policy
   local-repository-servers
   app-center
   software-monitor

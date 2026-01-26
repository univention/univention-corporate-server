.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-perform-updates:

Perform updates
===============

Nubus for UCS updates follow a structured process
that ensures system stability and consistency.
Before and after each update, special scripts run
to validate the system and perform necessary cleanup.
Understanding these scripts helps you troubleshoot issues
and ensures smooth updates across your infrastructure.

For information about UCS version numbering and release types,
see :ref:`lifecycle-versioning`.

Understand pre-update checks
-----------------------------

The pre-update script :file:`preup.sh` runs before every release update
to perform critical validation
to ensure the system is ready for the update
and that the update can complete successfully.

What it does
   The :program:`preup.sh` script checks for potential problems
   that could prevent a successful update or cause system instability.
   If it detects issues, it cancels the update in a controlled manner
   to protect your system.
   Among these checks are the following:

   * Disk space availability on essential file systems.
   * Package state consistency.
   * LDAP schema and connectivity validation.
   * Machine account credentials validation.
   * System compatibility checks.
   * Version compatibility across systems in the domain.

What happens if it fails
   When :program:`preup.sh` detects a problem,
   it reports the issue and stops the update process.
   This controlled interruption is preferable to an incomplete update
   that could compromise system stability.
   Review the error messages to identify and fix the underlying problem.

Understand post-update cleanup
------------------------------

The post-update script :file:`postup.sh` runs at the end of each update
to perform necessary cleanup operations
and ensure your system is fully consistent with the new version.

What it does
   The :command:`postup.sh` script performs cleanup and verification tasks
   after the update completes.
   These operations ensure the system is in a stable, consistent state
   and all changes are properly integrated.
   Common cleanup operations include the following:

   * Removing temporary installation files and backup package sources.
   * Restarting the firewall and *Management UI* for connectivity.
   * Updating system information in the LDAP directory.
   * Running role-specific configurations.
   * Removing deprecated package configurations.

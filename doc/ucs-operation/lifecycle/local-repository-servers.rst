.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-local-repository-servers:

Local repository servers
========================

A local repository mirrors packages from the Univention update server to your local infrastructure.
This enables you to manage updates independently of internet connectivity
and distribute packages efficiently across multiple systems.

.. _lifecycle-local-repository-benefits:

Benefits of using a local repository
   * Reduced bandwidth usage: Download updates once from Univention servers,
     then distribute to all systems locally,
     significantly reducing internet bandwidth consumption
     in environments with many systems.

   * Offline updates: Update systems without requiring internet access.
     This is useful for air-:spelling:word:`gapped` networks
     or locations with unreliable connectivity.

   * Faster deployments: Local package distribution is faster
     than downloading from remote servers,
     especially in geographically distributed environments
     or over slow network links.

   * Update control: Maintain a local copy of packages,
     giving you control over which versions are available
     and when systems can access them.

.. _lifecycle-local-repository-considerations:

Considerations for maintaining a local repository
   * Synchronization effort: You must regularly synchronize the local repository
     with upstream Univention servers
     to stay up to date with security and stability updates.

   * Administrative overhead: You must monitor repository health and manage synchronization.

.. _lifecycle-local-repository-choosing:

Choosing whether to use a local repository
   Use a local repository server when you manage multiple Nubus for UCS systems,
   particularly across distributed locations
   or with limited internet connectivity.
   For single-system installations or environments with reliable, high-bandwidth internet access,
   use online repositories directly.

Nubus for UCS automatically generates APT package sources
in the :file:`/etc/apt/sources.list.d/` directory
based on settings for release, errata updates, and add-on components.
If you need additional repositories on a system,
you can enter them in the :file:`/etc/apt/sources.list` file.

By default, new installations use the Univention repository at
``https://updates.software-univention.de``.

.. _lifecycle-local-repository-repo-package-status:

Repository package status
   Univention classifies packages in its repository as either *maintained* or *unmaintained*.
   All packages in the standard package scope are in *maintained* status.
   Univention provides security updates in a timely manner
   only for *maintained* packages.
   You can view the list of *maintained* packages on a Nubus for UCS system
   at :file:`/usr/share/univention-errata-level/maintained-packages.txt`.

   Univention doesn't provide security updates
   or other maintenance for *unmaintained* packages.
   To verify whether your system has *unmaintained* packages installed,
   run the :command:`univention-list-installed-unmaintained-packages` command.

.. _lifecycle-local-repository-repo-components:

Repository components
   To manage which repository components your system uses,
   configure the UCR variable
   :envvar:`repository/online/component/COMPONENTNAME`,
   where :samp:`{COMPONENTNAME}` is the name of the component.
   Set the variable to ``no`` to exclude a component from synchronization,
   or leave it unset to use the default behavior.

.. _lifecycle-local-repository-create:

Create and update a local repository
------------------------------------

This section describes how to create and maintain a synchronized local repository
with upstream Univention servers.

.. _lifecycle-local-repository-create-prerequisites:

Prerequisites
   To create a local repository, you need Root user credentials
   to run the repository commands in a terminal.

.. _lifecycle-local-repository-create-init:

Initialize the repository
   The :command:`univention-repository-create` command initializes a local repository
   and begins synchronization with upstream Univention servers.
   The command installs the :program:`univention-debmirror` package,
   if the system doesn't already have it.
   Synchronization time depends on your connection bandwidth
   and the repository size.
   The command also enables the local repository
   by setting the UCR variable :envvar:`local/repository` to ``yes``.

   .. TODO: Add repository size estimate once measurements are available from colleagues.

   To initialize the repository,
   run the command from :numref:`lifecycle-local-repository-create-figure` in a terminal.
   The command requires your confirmation to proceed.
   After confirmation, synchronization begins automatically.
   It stores the repository in the :file:`/var/lib/univention-repository/mirror/` directory by default.

   When initialization completes,
   the command shows instructions for configuring other systems.
   Follow these instructions to configure them to use this repository.

   .. code-block:: console
      :caption: Create a local repository
      :name: lifecycle-local-repository-create-figure

      $ univention-repository-create

   .. tip::

      Monitor synchronization progress in the repository log file:
      :file:`/var/log/univention/repository.log`

.. _lifecycle-local-repository-create-synchronize:

Synchronize the repository regularly
   After the initial repository creation,
   use the :command:`univention-repository-update` command to keep the repository
   synchronized with upstream Univention servers,
   as shown in :numref:`lifecycle-local-repository-update-figure`.
   Subsequent synchronization runs download only changed packages,
   so they're faster than the initial creation.

   .. code-block:: console
      :caption: Update a local repository
      :name: lifecycle-local-repository-update-figure

      $ univention-repository-update net

.. _lifecycle-local-repository-create-locations:

Synchronize repositories across locations
   You can also synchronize local repositories across multiple locations.
   For example,
   maintain a main repository at company headquarters
   and synchronize it to local repositories at individual locations.

.. _lifecycle-local-repository-create-multiple-locations:

Use a main repository for multiple locations
   When you manage Nubus for UCS systems across multiple locations,
   you can use a centralized main repository
   instead of having each location maintain its own repository.

   In this scenario,
   set up one main repository at your organization headquarters
   that synchronizes with upstream Univention servers.
   At each remote location,
   configure the systems to use the main repository as their repository server
   instead of synchronizing directly from upstream.

   Configure remote locations to use the main repository
   by setting the UCR variable :envvar:`repository/mirror/server`
   to the FQDN of the main repository on those systems.
   The systems still run :command:`univention-repository-update net` to synchronize locally,
   but they pull packages from your main repository instead of from upstream.

.. _lifecycle-local-repository-create-error-handling:

Error handling
   If the commands fail,
   check the following error codes:

   :Exit code 0: Command completed successfully.
   :Exit code 1: A configuration error occurred, or the user aborted the operation.
   :Exit code 5: Another updater process is already running; wait for completion and retry.

   For detailed error messages,
   validate the repository log file: :file:`/var/log/univention/repository.log`

.. _lifecycle-local-repository-configuration:

Configure the repository server
-------------------------------

After you create a local repository, you need to configure your systems to use it.
This section shows you three ways to do this: through the management module for individual systems,
through the Univention Configuration Registry for command-line configuration,
and through LDAP policies when you manage multiple systems centrally.

The default value for the repository server URL is ``https://updates.software-univention.de``.

.. _lifecycle-local-repository-management-module:

Configuration through management module
   In the *Repository Settings* management module,
   specify the *Repository server URL*.
   Find the module at :menuselection:`Software --> Repository Settings`.
   Use this approach for individual system configuration through the graphical interface.

.. _lifecycle-local-repository-ucr:

Configuration through Univention Configuration Registry
   You can specify the repository server URL in the UCR variable
   :external+uv-ucs-manual:envvar:`repository/online/server`.
   Use this approach for individual system configuration from the command line.

.. _lifecycle-local-repository-policy:

Policy-based configuration of the repository server
   You can also specify the repository server using the *Repository server* policy
   in the :external+uv-nubus-manual:ref:`nubus-computer-management`.
   The selection field shows only Nubus for UCS server systems
   with a configured DNS entry.
   Use this approach to configure multiple systems centrally in larger environments.

All configuration methods—the management module,
Univention Configuration Registry,
and policy-based configuration—modify the same system files:

* :file:`/etc/apt/sources.list.d/15_ucs-online-version.list`
* :file:`/etc/apt/sources.list.d/20_ucs-online-component.list`

To verify that your configuration is correct,
validate that the repository server URL in these files matches
the value in the UCR variable :envvar:`repository/online/server`.
The :file:`20_ucs-online-component.list` file only contains repository entries
when you configure components.

.. TODO: Add cross-reference to the components section once it is available and remove the space between the paragraphs.

:numref:`lifecycle-local-repository-verify-figure`
shows how the repository server URL appears in the file.

.. code-block:: text
   :caption: Repository server URL in :file:`sources.list.d` file (excerpt)
   :name: lifecycle-local-repository-verify-figure

   deb https://updates.software-univention.de/ ucs520 main

.. _lifecycle-local-repository-maintenance:

Maintain the local repository
-----------------------------

Regular maintenance ensures optimal performance and manages disk space efficiently.

.. _lifecycle-local-repository-maintenance-schedule:

Schedule synchronization
   Run repository synchronization weekly on Wednesday evening or Thursday morning
   to stay current with weekly upstream package updates.

   Configure the synchronization task using the
   :command:`univention-repository-update net` command
   through either Univention Configuration Registry or an LDAP-based scheduling policy.
   :numref:`lifecycle-local-repository-maintain-cron-figure`
   shows an example using UCR variables.
   The time format is ``hour minute day month weekday``.
   This example synchronizes the repository every Wednesday at 22:00 in your local time zone.
   Adjust the schedule based on your organizational needs
   and network traffic patterns.

   .. TODO: Add cross-reference to scheduling and cron section once it is available.

   .. code-block:: console
      :caption: Configure weekly repository synchronization via UCR
      :name: lifecycle-local-repository-maintain-cron-figure

      $ univention-config-registry set \
         cron/repository-sync/command='/usr/sbin/univention-repository-update net' \
         cron/repository-sync/time='22 * * * 3'

.. _lifecycle-local-repository-maintenance-monitor:

Monitor repository health
   After each synchronization,
   verify that it completed successfully.

   Check the exit code of the synchronization command—
   exit code ``0`` indicates success.
   Review the repository log file for error messages or warnings.
   If errors occur,
   consult the :ref:`lifecycle-local-repository-troubleshooting` section
   for diagnosis and resolution.

   Review disk usage to ensure sufficient space for future synchronizations.

.. _lifecycle-local-repository-maintenance-disk-space:

Manage disk space
   Disk usage grows over time as upstream adds package versions.
   Regular cleanup prevents disk space exhaustion.

   * Limit the version range using the UCR variables
     :envvar:`repository/mirror/version/start` and :envvar:`repository/mirror/version/end`.
     The system synchronizes only versions within this range.

   * Exclude optional components by setting the UCR variable
     :envvar:`repository/online/component/COMPONENTNAME` to ``no``,
     where :samp:`{COMPONENTNAME}` is the component name you want to deactivate.
     The system excludes this component from the next synchronization.

     .. TODO: Verify the UCR variable and add cross-reference to additional software section, when available.

   * Exclude source packages
     using the UCR variable
     :envvar:`repository/mirror/sources`
     if you don't require them,
     since source packages increase repository size significantly.

   * Prune old kernel packages using the :command:`univention-prune-kernels` command
     to remove outdated kernel packages and free disk space.

   .. warning::

      During synchronization,
      :program:`apt-mirror` requires temporary disk space
      in addition to the final repository size.
      Ensure at least 2x the expected mirror size in free disk space
      before running synchronization.

.. _lifecycle-local-repository-maintenance-review:

Review and plan
   Review your repository configuration
   and growth patterns quarterly
   to anticipate storage needs.

   Monitor repository size trends.
   If growth consistently approaches your disk capacity,
   consider expanding storage
   or adjusting your version retention policy.

   Verify that your version retention strategy
   matches your UCS support lifecycle.
   Univention provides security updates
   for *maintained* versions.
   Remove versions that are no longer in your support scope.

   Plan for major UCS releases
   in advance of their publication.
   Ensure adequate disk space
   before the release synchronization begins.

.. _lifecycle-local-repository-troubleshooting:

Troubleshooting repository problems
-----------------------------------

If you encounter issues when creating or updating a local repository,
use the following guidance to diagnose and resolve common problems.

Review the repository log file
:file:`/var/log/univention/repository.log`
for detailed error messages and diagnostic information.

.. _lifecycle-local-repository-troubleshooting-fails-to-start:

Repository creation or update fails to start
   The command returns exit code ``5``
   because another updater process is running.

   Verify if another :command:`univention-repository-create`,
   :command:`univention-repository-update`,
   or system update process is active on the system.
   Wait for the other process to complete,
   then retry your command.

.. _lifecycle-local-repository-troubleshooting-config-incorrect:

Configuration fails to apply or appears incorrect
   The command completes with exit code ``1``,
   or the system isn't using the configured repository server.

   Confirm that you set the following Univention Configuration Registry variables correctly:

   * :envvar:`local/repository` must have the value ``yes``.
   * :envvar:`repository/mirror/server` must have the value ``yes`` if you use a local repository.
   * :envvar:`repository/online/server` must point to the correct repository server URL.

   After you corrected any configuration,
   review the files to confirm the changes took effect:
   :file:`/etc/apt/sources.list.d/15_ucs-online-version.list`
   and :file:`/etc/apt/sources.list.d/20_ucs-online-component.list`.

.. _lifecycle-local-repository-troubleshooting-mirror-self:

Mirror server pointing to itself
   The command fails with exit code ``1`` when you configure the mirror server
   to point to the local system instead of an upstream repository server.

   Verify that the UCR variable :envvar:`repository/mirror/server`
   doesn't contain the FQDN of your local system.
   It must point to a valid upstream repository server,
   like ``https://updates.software-univention.de``.

.. _lifecycle-local-repository-troubleshooting-slow-stalls:

Synchronization is slow or stalls
   The initial repository synchronization downloads all packages
   and can take several hours
   depending on network bandwidth and repository size.

   If synchronization appears to stall,
   verify network connectivity to the repository server
   and ensure you have sufficient disk space on your system.

.. _lifecycle-local-repository-troubleshooting-unreachable:

Repository server unreachable
   Your system can't connect to the configured repository server.
   Verify the following:

   * Network connectivity exists from your system to the repository server.
   * DNS resolution works for the repository server hostname.
   * The repository server URL in the UCR variable :envvar:`repository/online/server` is correct.
   * Firewall rules allow access to the repository server.

.. _lifecycle-local-repository-troubleshooting-disk-space:

Insufficient disk space
   The system runs out of disk space during synchronization.

   Verify that you have sufficient disk space available
   in the directory you configured in the UCR variable :envvar:`repository/mirror/basepath`.
   The default path is :file:`/var/lib/univention-repository/`.

   The amount of space you need depends on
   which UCS versions and components you choose to mirror.

.. _lifecycle-local-repository-troubleshooting-permissions:

Not running with sufficient permissions
   The command fails when you don't run it with root privileges.
   Run all repository management commands as the ``root`` user.

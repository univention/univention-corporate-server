.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-repository-management:

Repository management
=====================

Repository management involves two interconnected decisions:
creating a local repository
and configuring your systems to use it.
Together, these decisions give you control over system updates.
This section covers the repository management workflow,
from setting up a local repository to maintaining it over time.

To create a local repository,
synchronize packages from upstream Univention servers
to your local infrastructure.
After you have a local repository,
you configure your systems to use it
instead of reaching out to remote servers.
These two steps are separate but deeply connected—you need both to manage updates independently.

This section covers three main topics:
creating and updating a local repository,
configuring your systems to use it,
and maintaining it for long-term stability.

.. _lifecycle-repository-management-local:

Local repository servers
------------------------

A local repository mirrors packages from the Univention update server to your local infrastructure.
This enables you to manage updates independently of internet connectivity
and distribute packages efficiently across multiple systems.

.. _lifecycle-repository-management-local-benefits:

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

.. _lifecycle-repository-management-local-considerations:

Considerations for maintaining a local repository
   * Synchronization effort: You must regularly synchronize the local repository
     with upstream Univention servers
     to stay up to date with security and stability updates.

   * Administrative overhead: You must monitor repository health and manage synchronization.

.. _lifecycle-repository-management-local-choosing:

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

.. _lifecycle-repository-management-local-repo-package-status:

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

.. _lifecycle-repository-management-local-repo-components:

Repository components
   To manage which repository components your system uses,
   configure the UCR variable
   :envvar:`repository/online/component/COMPONENTNAME`,
   where :samp:`{COMPONENTNAME}` is the name of the component.
   Set the variable to ``no`` to exclude a component from synchronization,
   or leave it unset to use the default behavior.

.. _lifecycle-repository-management-local-create:

Create and update a local repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to create and maintain a synchronized local repository
with upstream Univention servers.

.. _lifecycle-repository-management-local-create-prerequisites:

Prerequisites
   To create a local repository, you need Root user credentials
   to run the repository commands in a terminal.

.. _lifecycle-repository-management-local-create-init:

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
   run the command from :numref:`lifecycle-repository-management-local-create-figure` in a terminal.
   The command requires your confirmation to proceed.
   After confirmation, synchronization begins automatically.
   It stores the repository in the :file:`/var/lib/univention-repository/mirror/` directory by default.

   When initialization completes,
   the command shows instructions for configuring other systems.
   Follow these instructions to configure them to use this repository.

   .. code-block:: console
      :caption: Create a local repository
      :name: lifecycle-repository-management-local-create-figure

      $ univention-repository-create

   .. tip::

      Monitor synchronization progress in the repository log file:
      :file:`/var/log/univention/repository.log`

.. _lifecycle-repository-management-local-create-synchronize:

Synchronize the repository regularly
   After the initial repository creation,
   use the :command:`univention-repository-update` command to keep the repository
   synchronized with upstream Univention servers,
   as shown in :numref:`lifecycle-repository-management-local-update-figure`.
   Subsequent synchronization runs download only changed packages,
   so they're faster than the initial creation.

   .. code-block:: console
      :caption: Update a local repository
      :name: lifecycle-repository-management-local-update-figure

      $ univention-repository-update net

.. _lifecycle-repository-management-local-create-locations:

Synchronize repositories across locations
   You can also synchronize local repositories across multiple locations.
   For example,
   maintain a main repository at company headquarters
   and synchronize it to local repositories at individual locations.

.. _lifecycle-repository-management-local-create-multiple-locations:

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

.. _lifecycle-repository-management-local-create-error-handling:

Error handling
   If the commands fail,
   check the following error codes:

   :Exit code 0: Command completed successfully.
   :Exit code 1: A configuration error occurred, or the user aborted the operation.
   :Exit code 5: Another updater process is already running; wait for completion and retry.

   For detailed error messages,
   validate the repository log file: :file:`/var/log/univention/repository.log`

.. _lifecycle-repository-management-configuration:

Configure the repository server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you create a local repository, you need to configure your systems to use it.
This section shows you three ways to do this: through the management module for individual systems,
through the Univention Configuration Registry for command-line configuration,
and through LDAP policies when you manage multiple systems centrally.

The default value for the repository server URL is ``https://updates.software-univention.de``.

.. _lifecycle-repository-management-local-management-module:

Configuration through management module
   In the *Repository Settings* management module,
   specify the *Repository server URL*.
   Find the module at :menuselection:`Software --> Repository Settings`.
   Use this approach for individual system configuration through the graphical interface.

.. _lifecycle-repository-management-local-ucr:

Configuration through Univention Configuration Registry
   You can specify the repository server URL in the UCR variable
   :external+uv-ucs-manual:envvar:`repository/online/server`.
   Use this approach for individual system configuration from the command line.

.. _lifecycle-repository-management-local-policy:

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

:numref:`lifecycle-repository-management-local-verify-figure`
shows how the repository server URL appears in the file.

.. code-block:: text
   :caption: Repository server URL in :file:`sources.list.d` file (excerpt)
   :name: lifecycle-repository-management-local-verify-figure

   deb https://updates.software-univention.de/ ucs520 main

.. _lifecycle-repository-management-maintenance:

Maintain the local repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Regular maintenance ensures optimal performance and manages disk space efficiently.

.. _lifecycle-repository-management-maintenance-schedule:

Schedule synchronization
   Run repository synchronization weekly on Wednesday evening or Thursday morning
   to stay current with weekly upstream package updates.

   Configure the synchronization task using the
   :command:`univention-repository-update net` command
   through either Univention Configuration Registry or an LDAP-based scheduling policy.
   :numref:`lifecycle-repository-management-maintain-cron-figure`
   shows an example using UCR variables.
   The time format is ``hour minute day month weekday``.
   This example synchronizes the repository every Wednesday at 22:00 in your local time zone.
   Adjust the schedule based on your organizational needs
   and network traffic patterns.

   .. TODO: Add cross-reference to scheduling and cron section once it is available.

   .. code-block:: console
      :caption: Configure weekly repository synchronization via UCR
      :name: lifecycle-repository-management-maintain-cron-figure

      $ univention-config-registry set \
         cron/repository-sync/command='/usr/sbin/univention-repository-update net' \
         cron/repository-sync/time='22 * * * 3'

.. _lifecycle-repository-management-maintenance-monitor:

Monitor repository health
   After each synchronization,
   verify that it completed successfully.

   Check the exit code of the synchronization command—
   exit code ``0`` indicates success.
   Review the repository log file for error messages or warnings.
   If errors occur,
   consult the :ref:`lifecycle-repository-management-troubleshooting` section
   for diagnosis and resolution.

   Review disk usage to ensure sufficient space for future synchronizations.

.. _lifecycle-repository-management-maintenance-disk-space:

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

.. _lifecycle-repository-management-maintenance-review:

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

.. _lifecycle-repository-management-troubleshooting:

Troubleshooting repository problems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you encounter issues when creating or updating a local repository,
use the following guidance to diagnose and resolve common problems.

Review the repository log file
:file:`/var/log/univention/repository.log`
for detailed error messages and diagnostic information.

.. _lifecycle-repository-management-troubleshooting-fails-to-start:

Repository creation or update fails to start
   The command returns exit code ``5``
   because another updater process is running.

   Verify if another :command:`univention-repository-create`,
   :command:`univention-repository-update`,
   or system update process is active on the system.
   Wait for the other process to complete,
   then retry your command.

.. _lifecycle-repository-management-troubleshooting-config-incorrect:

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

.. _lifecycle-repository-management-troubleshooting-mirror-self:

Mirror server pointing to itself
   The command fails with exit code ``1`` when you configure the mirror server
   to point to the local system instead of an upstream repository server.

   Verify that the UCR variable :envvar:`repository/mirror/server`
   doesn't contain the FQDN of your local system.
   It must point to a valid upstream repository server,
   like ``https://updates.software-univention.de``.

.. _lifecycle-repository-management-troubleshooting-slow-stalls:

Synchronization is slow or stalls
   The initial repository synchronization downloads all packages
   and can take several hours
   depending on network bandwidth and repository size.

   If synchronization appears to stall,
   verify network connectivity to the repository server
   and ensure you have sufficient disk space on your system.

.. _lifecycle-repository-management-troubleshooting-unreachable:

Repository server unreachable
   Your system can't connect to the configured repository server.
   Verify the following:

   * Network connectivity exists from your system to the repository server.
   * DNS resolution works for the repository server hostname.
   * The repository server URL in the UCR variable :envvar:`repository/online/server` is correct.
   * Firewall rules allow access to the repository server.

.. _lifecycle-repository-management-troubleshooting-disk-space:

Insufficient disk space
   The system runs out of disk space during synchronization.

   Verify that you have sufficient disk space available
   in the directory you configured in the UCR variable :envvar:`repository/mirror/basepath`.
   The default path is :file:`/var/lib/univention-repository/`.

   The amount of space you need depends on
   which UCS versions and components you choose to mirror.

.. _lifecycle-repository-management-troubleshooting-permissions:

Not running with sufficient permissions
   The command fails when you don't run it with root privileges.
   Run all repository management commands as the ``root`` user.

.. _lifecycle-repository-management-custom-package-sources:

Custom package sources
----------------------

You selected software components during setup based on your organization's needs.
These components cover the core functionality required to operate the system.
However, you may need to install additional packages
to extend Nubus for UCS with functionality beyond the initial setup.
These optional packages aren't required for core operations—they're extra capabilities
that your organization might need for specific services or integrations.
When you install a package, the package manager automatically resolves and installs
any package dependencies,
so you don't need to manually identify and install supporting packages.

If you need to install software that isn't available as a Debian package,
place it in the :file:`/opt/` or :file:`/usr/local/` directories.
Use these directories to keep your custom software separate from Univention packages
and maintain a clean system architecture.

.. _lifecycle-repository-management-custom-package-method:

Choose your installation method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have several options to install additional packages on your Nubus for UCS system.
Each method serves different administrative needs and preferences.
All methods draw from the same package repositories,
so the packages available to you are the same regardless of which method you choose.

.. _lifecycle-repository-management-custom-package-method-appcenter:

Univention App Center
   Univention App Center offers a graphical interface where you can browse, search,
   and install applications and UCS components.
   You can choose from applications provided by Univention and third-party vendors
   for specific use cases and integration scenarios.
   For details, see :ref:`lifecycle-repository-management-custom-package-appcenter`.

.. _lifecycle-repository-management-custom-package-method-umc:

Package Management
   The *Package Management* module in the *Management UI* lets you search for and install
   individual Debian packages.
   For details, see :ref:`lifecycle-repository-management-custom-package-umc`.

.. _lifecycle-repository-management-custom-package-method-commandline:

Command line
   The command line provides direct control over package management.
   Use the command line when you prefer scripting or need access to advanced options.
   For details, see :ref:`lifecycle-repository-management-custom-package-commandline`.

.. _lifecycle-repository-management-custom-package-appcenter:

Installation through Univention App Center
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Univention App Center hosts UCS components alongside applications from Univention
and third-party vendors.
You can install or remove UCS components directly from the App Center.
For a glimpse on the App Center overview,
see :numref:`lifecycle-repository-management-custom-package-appcenter-figure`.
To learn more about the App Center and its capabilities,
see :external+uv-ucs-manual:ref:`software-appcenter`
in :cite:t:`ucs-manual`.

.. TODO: Add cross-reference to App Center chapter once it exists.

.. _lifecycle-repository-management-custom-package-appcenter-figure:

.. figure:: /images/appcenter_overview.*
   :alt: UCS components and other apps in the App Center

   UCS components and other apps in the App Center

.. _lifecycle-repository-management-custom-package-umc:

Installation through Management UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the *Package Management* module,
you need web access to the *Management UI*
and the ``Domain Admins`` group must include your user account.

The *Package Management* module in the *Management UI* provides a graphical interface
to search for and install individual Debian packages.
To open it,
navigate to :menuselection:`Software --> Package Management`.

To find packages, you search by name or description.
The search results display matching packages in a table
with their names, descriptions, and installation status.
Click an entry to view more details,
then use the actions to install, uninstall,
or upgrade the package.
:numref:`lifecycle-repository-management-custom-package-umc-figure`
shows package details.

Action buttons
   :Install: Select to install a package that isn't yet installed.
   :Uninstall: Select to uninstall an installed package.
   :Upgrade: Select to upgrade an installed package with an available update.
   :Close: Select to return to your previous search.

.. _lifecycle-repository-management-custom-package-umc-figure:

.. figure:: /images/software_install.*
   :alt: Installing the package univention-squid through Package Management module

   Installing the package :program:`univention-squid` through Package Management module

.. _lifecycle-repository-management-custom-package-commandline:

Installation from command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the command line when you prefer working directly in the terminal.
You need ``root`` user rights to perform package management actions.
For interactive actions, use the :command:`univention-install`.
For automation and integration in scripts,
use the :command:`apt-get` command instead of :command:`univention-install`.

.. _lifecycle-repository-management-custom-package-commandline-install:

Install
   To install a package, use the :command:`univention-install` command
   in :numref:`lifecycle-repository-management-custom-package-commandline-install-listing`.

   .. code-block:: console
      :caption: Install a package with :command:`univention-install`
      :name: lifecycle-repository-management-custom-package-commandline-install-listing

      $ univention-install <PACKAGENAME>

.. _lifecycle-repository-management-custom-package-commandline-remove:

Remove
   To remove a package, use the :command:`univention-remove` command
   in :numref:`lifecycle-repository-management-custom-package-commandline-remove-listing`.

   .. code-block:: console
      :caption: Remove a package with :command:`univention-remove`
      :name: lifecycle-repository-management-custom-package-commandline-remove-listing

      $ univention-remove <PACKAGENAME>

.. _lifecycle-repository-management-custom-package-commandline-usage:

Usage
   To view options and usage information for either command,
   add the ``--help`` flag
   as in :numref:`lifecycle-repository-management-custom-package-commandline-help-listing`.

   .. code-block:: console
      :caption: Display help for :command:`univention-install`
      :name: lifecycle-repository-management-custom-package-commandline-help-listing

      $ univention-install --help
      $ univention-remove --help

.. _lifecycle-repository-management-custom-package-commandline-search:

Search
   To search for available packages by name or description,
   use :command:`apt-cache search`
   as in :numref:`lifecycle-repository-management-custom-package-commandline-search-listing`.
   This command lists all packages matching your search term in their name or description.

   .. code-block:: console
      :caption: Search for packages
      :name: lifecycle-repository-management-custom-package-commandline-search-listing

      $ apt-cache search fax

.. _lifecycle-repository-management-custom-package-hooks:

Automate tasks around app actions with hook scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use hook scripts to automate tasks
that run after you install, upgrade, or remove applications through Univention App Center.
Hook scripts are custom shell scripts that run at specific lifecycle events.
This feature is for advanced administrators
who understand shell scripting and app identifiers—the ``appid``.

.. important::

   Hook scripts only apply to applications installed through the App Center,
   not to individual Debian packages.

Prerequisites
   To use hook scripts, you need:

   * ``root`` user access on the system.
   * Shell scripting knowledge.
   * Understanding of the app identifier ``appid`` for your target app.

How hook scripts work
   When you install, upgrade, or remove an App Center application,
   the system looks for hook scripts in specific directories and runs them automatically.
   Each hook script phase corresponds to a lifecycle event:

   :Post-install: Runs after you install the app.
   :Post-upgrade: Runs after you update the app.
   :Post-remove: Runs after you remove the app.

Storing hook scripts
   Place your custom hook scripts in one of these directories.
   Replace :samp:`{{appid}}` with the identifier of your target app.

   * :file:`/var/lib/univention-appcenter/apps/{{appid}}/local/hooks/post-install.d/`
   * :file:`/var/lib/univention-appcenter/apps/{{appid}}/local/hooks/post-upgrade.d/`
   * :file:`/var/lib/univention-appcenter/apps/{{appid}}/local/hooks/post-remove.d/`


File requirements
   * Names must contain only lowercase letters and numbers, regular expression: ``^[a-z0-9]+$``.
   * Mark the scripts executable: :command:`chmod +x filename`.
   * :program:`run-parts` runs the scripts in order.

Practical examples
   You might use hook scripts for tasks like the following:

   * Restart a service after installation.
   * Configure application-specific settings in a post-install script.
   * Back up configuration files or persistent data before removal.
   * Clean up temporary files in a post-remove script.

Testing and troubleshooting
   To test which scripts would execute in a directory without running them,
   use the command shown in :numref:`lifecycle-repository-management-custom-package-hooks-test`.
   Script errors and diagnostic messages appear in :file:`/var/log/univention/appcenter.log`.
   For more information, see :command:`man run-parts`.

   .. code-block:: console
      :caption: Test hook scripts without executing them
      :name: lifecycle-repository-management-custom-package-hooks-test

      $ run-parts --test /var/lib/univention-appcenter/apps/appid/local/hooks/post-install.d/

Security and permissions
   * Set appropriate file ownership, typically ``root:root``.
   * Use restrictive permissions, typically ``0755`` for executable scripts.
   * Avoid world-writable scripts to prevent unauthorized modification.
   * Validate inputs and sanitize variables in your scripts.

.. _lifecycle-repository-management-custom-package-policy:

Centralized package management with policies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This approach suites organizations
that manage multiple system centrally
and need consistent deployments to reduce manual effort and prevent configuration drift.

.. _lifecycle-repository-management-custom-package-policy-when-use:

When to use policies
   Use policies when you need to:

   * Deploy identical packages to multiple systems consistently.
   * Manage packages for different roles or departments separately.
   * Scale package management across growing numbers of systems.
   * Maintain package configurations across multiple locations or departments.

.. _lifecycle-repository-management-custom-package-policy-prerequisites:

Prerequisites
   To work with package policies, you need:

   * The ``Domain Admins`` group must include your user account.
   * Access to the *Management UI*.
   * Understanding of your system's organizational structure in form of containers and organizational units in the directory service.

.. _lifecycle-repository-management-custom-package-policy-create:

How to find and create policies
   You manage package policies through the *Management UI*.
   To create a policy, use the following steps:

   #. Open the *Management UI*

   #. Navigate to :menuselection:`Domain --> Policies`.

   #. To create a policy, click :guilabel:`Add`.

   #. Select the package policy type for your system role,
      for example *Policy: Packages for Managed Nodes*.

   #. Choose the container where to store the policy.

   #. Click :guilabel:`Next`

      The *General* tab shows fields for the selected policy type.
      The *Advanced* settings tab provides additional configuration options.

   #. Click :guilabel:`Save` to finally create the policy.

.. _lifecycle-repository-management-custom-package-policy-fields:

Understanding policy fields
   Each package policy has the following main fields:

   .. _lifecycle-repository-management-custom-package-policy-fields-name:

   Name
      An unambiguous name for the policy,
      for example *Database Server Packages* or *Development Team Workstations*.

   .. _lifecycle-repository-management-custom-package-policy-fields-install:

   Package installation list
      A list of package names to install.
      Example: :samp:`postgresql postgresql-contrib mysql-server`

   .. _lifecycle-repository-management-custom-package-policy-fieldkes-remove:

   Package removal list
      A list of packages to remove.
      Example: :samp:`xserver apache2`

.. _lifecycle-repository-management-custom-package-policy-scope:

Scope and limitations
   Package policies inherit down the directory container hierarchy.
   Nubus applies the policy values defined closest to the object.
   For detailed information about policy inheritance, conflict resolution,
   and advanced policy options,
   see :external+uv-nubus-manual:ref:`nubus-domain-policies`
   in :cite:t:`uv-nubus-manual`.

.. _lifecycle-repository-management-custom-package-policy-scaling:

Managing packages at scale
   When you manage multiple systems across multiple locations or departments
   keep the following recommendations in mind:

   * Create separate policies for each role or department to maintain clear ownership.
   * Use meaningful policy names that indicate their purpose and scope.
   * Test policies on a small group of systems before you deploy them organization-wide.
   * Document which policies apply to which containers or organizational units.
   * Use the *Referencing objects* section in a policy to verify which systems have the policy applied.

.. _lifecycle-repository-management-custom-package-policy-timing:

Installation timing
   The maintenance policy defines the time when Nubus for UCS installs or removes packages.
   For configuration details,
   see :external+uv-ucs-manual:ref:`computers-softwaremanagement-maintenance-policy`.
   Nubus registers all packages from policies in the LDAP directory
   to make them available for management across the entire domain.

   .. TODO: Replace cross-reference with internal reference after section exists.

.. _lifecycle-repository-management-custom-package-policy-examples:

.. seealso::

   For more information about policies in general,
   including policy creation, assignment, and advanced settings,
   see :external+uv-nubus-manual:ref:`nubus-domain-policies`
   in :cite:t:`uv-nubus-manual`.

   For information about computer management in your domain,
   see :external+uv-nubus-manual:ref:`nubus-computer-management`
   in :cite:t:`uv-nubus-manual`.

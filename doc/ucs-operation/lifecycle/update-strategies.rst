.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-update-strategies:

Update strategies
=================

Keeping your Nubus for UCS systems current with the latest updates is essential for security,
stability, and access to new features. Depending on your environment and operational needs,
you can choose from different update strategies and methods.

You can update Nubus for UCS systems in two ways:
by updating individual systems using the *Software update* management module
or the command line.
To update multiple systems at once, use a computer policy.

.. _lifecycle-update-strategies-multiple-systems-environments:

Planning updates in multiserver environments
--------------------------------------------

When you update multiple UCS systems,
you need to plan your update order carefully.
The Primary Directory Node holds the authoritative LDAP directory service
and replicates it to all other LDAP servers in your domain.
Because :external+uv-ucs-manual:ref:`domain-ldap-schema` can change during release updates,
you **must always update the Primary Directory Node first**.

.. TODO: Replace reference to LDAP schema after it's available in the document.

Whenever possible, update all your Nubus for UCS systems in a single maintenance window.
If you can't do this,
ensure that any systems you haven't updated are no more
than one minor version older than your Primary Directory Node.
For information about the versioning,
see :ref:`lifecycle-versioning-release-types`.

.. _lifecycle-update-strategies-methods:

Update methods
--------------

You have three ways to perform updates:
through the graphical interface with the *Management UI*,
the command line, or using automated policies.
Choose the method appropriate for your environment and operational needs.

Regardless of the update method that you decide on,
the system writes all messages from the update process to
the :file:`/var/log/univention/updater.log` file.

.. _lifecycle-update-strategies-methods-management-module:

Update through the management module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use the *Software update* management module in the *Management UI*
to install both release updates and errata updates on your system.

:numref:`lifecycle-update-strategies-methods-management-module-figure`
shows the overview page of the management module.

.. _lifecycle-update-strategies-methods-management-module-figure:

.. figure:: /images/software_onlineupdate.*
   :alt: Updating a Nubus for UCS system through the 'Software update' management module

   Updating a Nubus for UCS system through the *Software update* management module

To install release updates, perform these steps:

#. :ref:`Sign in <ucs-operation-auth-sign-in>`
   to the *Management UI* with a user account in the ``Domain Admins`` group,
   such as ``Administrator``.

#. Navigate to :menuselection:`Software --> Software update`.

#. To refresh the package sources,
   click :guilabel:`Check for package updates`.
   Use this, for example, when a component provides an updated version.

Release updates
   The *Release updates* section shows the installed version
   and updates available Nubus for UCS versions.

   To update to the selected target version,
   click :guilabel:`Install release updates`.
   Nubus for UCS shows update notes
   with information about service restrictions during the update
   and asks you to confirm the update.
   The system automatically installs all intermediate versions needed
   to reach your selected version.

Package updates
   The *Package updates* section shows the available errata updates.

   To install errata updates,
   click :guilabel:`Install available errata updates`.
   This installs all available errata updates for your current release
   and installed components.

.. _lifecycle-update-strategies-methods-command-line:

Update through the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You must have ``root`` user rights and work on a terminal
to perform the following steps.

Run the :command:`univention-upgrade` command to update your system.
This command does the following:

#. Checks for available release or application updates.
#. Prompts you to confirm the installation.
#. Installs the updates, including any package updates, such as errata updates.

.. important::

   Avoid updating remotely over SSH,
   as network disconnections can interrupt the update.
   If you must update over a network connection,
   use :program:`screen` or :program:`at`
   to ensure the update continues despite network issues.
   All system roles have both programs installed.

.. _lifecycle-update-strategies-methods-policy:

Update through a policy
~~~~~~~~~~~~~~~~~~~~~~~

You can configure automatic updates for multiple computers at once
using an *Automatic updates* policy.
Use this policy in the
:external+uv-nubus-manual:ref:`nubus-computer-management`
or :external+uv-nubus-manual:ref:`nubus-domain-ldap`
management module.
For information about policies,
see :external+uv-nubus-manual:ref:`nubus-domain-policies`
in :cite:t:`uv-nubus-manual`.

:numref:`lifecycle-update-strategies-methods-policy-figure`
shows a typical policy configuration:

.. _lifecycle-update-strategies-methods-policy-figure:

.. figure:: /images/software_policy.*
   :alt: Updating UCS systems using an update policy

   Updating UCS systems using an update policy

To update Nubus for UCS through a policy,
configure the following settings:

#. :external+uv-nubus-manual:ref:`nubus-domain-policies-create`.
   Choose the policy type *Policy: Automatic updates*.

#. Activate the *Activate release updates* field to enable release updates.

#. Enter a version number in the *Update to this UCS version* field,
   for example ``5.2-4``.
   If you leave this blank, systems update to the highest available version.

#. Set the update schedule using a *Maintenance* policy,
   see
   :external+uv-ucs-manual:ref:`computers-softwaremanagement-maintenance-policy`.

#. Finally, you need to assign the policy,
   see :external+uv-nubus-manual:ref:`nubus-domain-policies-assign`.

.. _lifecycle-update-strategies-post-processing:

Post-processing after release updates
-------------------------------------

After you complete a release update,
you must verify
whether you need to run new or updated join scripts.

You can verify and run join scripts in the following ways:

* Use the *Domain join* management module in the *Management UI*.
* Run the command-line program :command:`univention-run-join-scripts`.

For details on join script management,
see :external+uv-ucs-manual:ref:`linux-domain-join`
in :cite:t:`ucs-manual`.

.. TODO: Replace cross reference about UCS domain join with internal reference.

.. _lifecycle-update-strategies-troubleshooting:

Troubleshooting update problems
-------------------------------

If you encounter problems during an update, use these resources to diagnose the issue:

Update log
   The system writes detailed messages to :file:`/var/log/univention/updater.log`.
   Review this file first for error messages and diagnostic information.

Configuration registry backup
   Before the update, the system saves the status of all Univention configuration registry variables to
   :file:`/var/univention-backup/update-to-{<TARGETRELEASEVERSION>}/`.
   Use this directory to verify which configuration values changed during the update.

   This information helps you identify
   whether the update completed correctly
   and which system configurations it affected.

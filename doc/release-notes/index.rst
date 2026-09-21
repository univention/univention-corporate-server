.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

############################################################################################
Release notes for the installation and update of Univention Corporate Server (UCS) |release|
############################################################################################

Publication date of UCS |release|: 2026-09-22

.. _relnotes-highlights:

******************
Release highlights
******************

|UCSUCS| |release| is available.
It includes feature improvements, extensions, and bug fixes.
The following overview highlights the most important changes:

New RADIUS authentication helper:
   WLAN authentication with username and password
   through the Nubus RADIUS service uses an authentication helper plugin internally.
   This helper has caused high CPU consumption in large environments.
   A rewrite of the helper module in Rust reduces CPU consumption
   and increases the number of authentications that each UCS installation can process.
   For more information, see :uv:bug:`59042`.

New Guardian backend based on :spelling:word:`Cerbos`:
   The Nubus *Authorization Service*, called Guardian, now uses the open source solution
   :program:`Cerbos` as its backend.
   It replaces the Open Policy Agent (OPA) backend.
   :program:`Cerbos` includes features that Guardian needs to make authorization decisions.
   More information about the authorization decisions will become available
   in the Univention public blog shortly after this release.
   Besides the :program:`Cerbos` backend,
   the *Authorization Service* is now available as a component of UCS,
   packaged as a Debian package that contains a container.
   This simplifies setup and maintenance compared with the former Docker Compose-based App Center app.

Improved handling of password hashes and optional removal of weaker hashes:
   In preparation for the removal of weaker password hashes,
   UCS |release| integrates several improvements.
   UDM now has more configuration options
   to define which hashing algorithms to use during password storage.
   These options let you remove weaker hashes that are still stored for compatibility reasons.
   The Active Directory Connection now supports more configurations
   in which Active Directory is configured with reduced encryption types.

Keycloak Metrics:
   The Keycloak app now lets you activate the integrated "Metrics Endpoint" in Keycloak.
   Administrators can get detailed information about Keycloak usage and events
   in their Prometheus and Grafana dashboards.
   For more information, see :external+uv-keycloak-app:ref:`use-case-metrics-monitoring` in
   :cite:t:`ucs-keycloak-doc`.

Education Classes support in the Microsoft 365 Connector:
   The *Microsoft 365 Connector* now lets you activate "educational classes"
   in Microsoft 365.
   Administrators of Nubus or UCS\@school can decide
   which groups to activate automatically,
   so that they don't need to administer the feature manually in Microsoft 365.
   For more information, see :external+uv-manual:ref:`idmcloud-o365-education-classes` in :cite:t:`ucs-manual`.

.. _relnotes-update:

**********************
Notes about the update
**********************

Before updating,
test the update in a separate test environment
that's identical to your production environment.
Run the update in a maintenance window,
because some services in the domain can be unavailable temporarily.

The update can take anywhere from 30 minutes to several hours,
depending on system performance, network connection, and installed software.
For large environments,
consult :cite:t:`ucs-performance-guide`.

.. warning::

   As of this release, disabling a user account no longer invalidates its password hash.
   Instead, account deactivation is enforced during LDAP bind, where a server-side check rejects disabled accounts.

   All services and Apps available for UCS support, including

   * services that authenticate via LDAP bind,
   * services using token- or OIDC-based authentication,
   * OX App Suite on UCS and
   * standard UCS mail services

   are not affected and require no changes by the operator.

   However, services that use password-lookup mode,
   where the service reads the ``userPassword`` hash and verifies it locally
   instead of performing a user bind (for example, Dovecot without ``auth_bind = yes``),
   will bypass this check.
   As a result, a disabled user providing the correct password would still be authenticated.

   If you operate such a service, you must either:

   1. Switch to LDAP bind authentication (e.g., set ``auth_bind = yes`` in Dovecot), or
   2. Update your LDAP lookup filter to exclude disabled accounts (e.g., using ``(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))``).

   Otherwise, disabled accounts will retain access through these services.

.. _relnotes-sequence:

Updating multiple UCS systems
=============================

In environments with multiple UCS systems,
the |UCSPRIMARYDN| must always be the first system in the update order
during a release update.

For more information about planning updates in multi server environments,
see :external+uv-ucs-operation:ref:`lifecycle-update-strategies-multiple-systems-environments`
in :cite:t:`uv-ucs-operation`.

.. _relnotes-bootloader:

********************************************************
Simultaneous operation of UCS and Debian on UEFI systems
********************************************************

Simultaneous operation of UCS and Debian GNU/Linux on UEFI systems
isn't supported in UCS 5.0 and later.

The GRUB boot loader of |UCSUCS| uses the same configuration files as Debian.
If Debian is already installed,
UCS can't boot after you install or update to UCS 5.0.
Conversely,
installing Debian after you install UCS 5.0
prevents UCS from booting.

For more information,
refer to :uv:kb:`17768`.

.. _relnotes-prepare:

*********************
Prepare for an update
*********************

This section covers important considerations before you update.

.. _relnotes-sufficient-disc-space:

Sufficient disk space
=====================

Ensure you have sufficient disk space for the update.
A standard installation requires 6 to 10 GB.
The update process requires an additional 1 to 2 GB
to download and install packages,
depending on your existing installation size.

.. _relnotes-console-for-update:

Console usage for update
========================

Sign in to the system's local console as ``root``
and run the update.
Alternatively,
you can run the update using |UCSUMC|.

If you run the update over a network connection,
take steps to ensure that the update continues if the connection is interrupted.
Network interruptions can cancel the update,
which severely affects the system.

Use tools such as :command:`tmux`, :command:`screen`, or :command:`at`
to keep the update running through network interruptions.
All UCS system roles have these tools installed by default.

.. _relnotes-pre-update-checks:

Script to check for known update issues
=======================================

Univention provides a script
that checks for problems
that could prevent a successful update.
You can download the script before the update
and run it on the UCS system.

.. code-block:: console

   # download
   $ curl -OOf https://updates.software-univention.de/download/univention-update-checks/pre-update-checks-5.2-7{.gpg,}

   # verify and run script
   $ apt-key verify pre-update-checks-5.2-7{.gpg,} && bash pre-update-checks-5.2-7

   ...

   Starting pre-update checks ...

   Checking app_appliance ...                        OK
   Checking block_update_of_NT_DC ...                OK
   Checking cyrus_integration ...                    OK
   Checking disk_space ...                           OK
   Checking hold_packages ...                        OK
   Checking ldap_connection ...                      OK
   Checking ldap_schema ...                          OK
   ...


.. _relnotes-post:

*****************************
Post processing of the update
*****************************

After the update,
run new or updated join scripts.
Either use the :guilabel:`Domain join` management module in the *Management UI*
or run :command:`univention-run-join-scripts` as ``root``.

Verify that the join scripts completed successfully.
Then restart the UCS system.

.. _relnotes-packages:

**************************
Notes on selected packages
**************************

The following sections cover selected packages for this update.

.. _relnotes-usage:

Collection of usage statistics
==============================

When you use UCS Core Edition,
UCS collects anonymous usage statistics for |UCSUMC|.
The system logs which modules you open
to a *Matomo* instance.
These statistics help Univention
improve |UCSUMC| development
based on customer needs.

You can verify the license status through the menu entry
:menuselection:`License --> License information`
in the user menu of |UCSUMC|.
If the *License information*
lists ``UCS Core Edition`` under *License type*,
your UCS system is using UCS Core Edition.

UCS doesn't collect usage statistics
if you use an `Enterprise Subscription <https://www.univention.com/products/prices-and-subscriptions/>`_
license such as *UCS Base Subscription* or *UCS Standard Subscription*.

To deactivate usage statistics collection,
set the |UCSUCRV| :envvar:`umc/web/piwik` to ``false``.

.. _relnotes-browsers:

Recommended browsers for |UCSUMC|
=================================

|UCSUMC| uses JavaScript and CSS features to display the web interface.
Your web browser must support cookies.
|UCSUMC| requires one of the following browsers:

* Chrome version 131 and later

* Firefox version 128 and later

* Safari and Safari Mobile version 18 and later

* Microsoft Edge version 128 and later

Older browsers can display the web interface incorrectly or cause functionality issues.

.. _relnotes-changelog:

*********
Changelog
*********

You can find the changes since UCS 5.2-6 in
:external+uv-changelog-5.2-7:doc:`index`.

.. _biblio:

************
Bibliography
************

.. bibliography::

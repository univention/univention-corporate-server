.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

############################################################################################
Release notes for the installation and update of Univention Corporate Server (UCS) |release|
############################################################################################

Publication date of UCS |release|: 2026-06-16

.. _relnotes-highlights:

******************
Release highlights
******************

|UCSUCS| 5.2-6 is available.
It includes feature improvements, extensions, and bug fixes.
The following overview highlights the most important changes:

* The *UDM HTTP REST API* now includes a metrics endpoint.
  You can retrieve basic Nubus metrics,
  such as the number of users, the software version, and the license status.
  Use these metrics in standard tools such as *Prometheus* and *Grafana*
  to improve observability.

  For more information, see :external+uv-nubus-manual:ref:`nubus-metrics`
  in :cite:t:`uv-nubus-manual`.

* |UCSUMC| includes a new section
  with technical details for objects in |UCSUDM|.
  You can view and search technical identifiers
  and the creation and modification timestamps for all objects.

* Groups in Univention Nubus
  can now have alternative email addresses in addition to a primary email address.
  You can use them as email aliases for groups,
  following the same concept as alternative email addresses for users.
  The Univention mail stack supports this additional attribute
  and delivers email sent to a group's alternative email address
  to all members of the group.

* Samba has been updated to version 4.24.2, including the latest security
  patches, so it's equivalent to version 4.24.3.

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

.. _relnotes-sequence:

Updating multiple UCS systems
=============================

In environments with multiple UCS systems,
follow the update sequence described later.

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
installing Debian after UCS 5.0
prevents UCS from booting.

For more information,
refer to :uv:kb:`17768`.

.. _relnotes-prepare:

******************
Prepare for update
******************

This section covers important considerations before you update.

.. _relnotes-sufficient-disc-space:

Sufficient disk space
=====================

Ensure you have sufficient disk space available for the update.
A standard installation requires a minimum of 6 to 10 GB.
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
take steps to ensure it continues if the connection is interrupted.
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
   $ curl -OOf https://updates.software-univention.de/download/univention-update-checks/pre-update-checks-5.2-6{.gpg,}

   # verify and run script
   $ apt-key verify pre-update-checks-5.2-6{.gpg,} && bash pre-update-checks-5.2-6

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
Use either the :guilabel:`Domain join` management module in the *Management UI*
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

When using UCS Core Edition,
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
lists ``UCS Core Edition`` under *License type*,
your UCS system is using UCS Core Edition.

UCS doesn't collect usage statistics
if you use an `Enterprise Subscription
<https://www.univention.com/products/prices-and-subscriptions/>`_
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

Older browsers may not display correctly or perform as expected.

.. _relnotes-changelog:

*********
Changelog
*********

You can find the changes since UCS 5.2-5 in
:external+uv-changelog-5.2-6:doc:`index`.

.. _biblio:

************
Bibliography
************

.. bibliography::

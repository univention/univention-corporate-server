.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

############################################################################################
Release notes for the installation and update of Univention Corporate Server (UCS) |release|
############################################################################################

Publication date of UCS |release|: 2024-FIXME

.. _relnotes-highlights:

******************
Release highlights
******************

With |UCSUCS| 5.2-0, the first minor release for |UCSUCS| (UCS) 5 is
available. It provides several feature improvements and extensions, new
properties as well as various improvements and bug fixes. Here is an overview of
the most important changes:

* Keycloak replaces SimpleSAMLPHP.

* No support for mixed UCS 4.x / UCS 5.x environments.

* Update from Python 3.7 to Python 3.11.
  No more support for Python 2.

* FIXME


UCS 5.2 is based on Debian 12 Bookworm.
As UCS 5.0 was based on Debian 10 Buster, there exists the intermediate UCS 5.1 based on Debian 11 Bullseye.
This is only required for updating and should never be used in production.
**No support!**

.. _relnotes-update:

**********************
Notes about the update
**********************

Run the update in a maintenance window, because some services in the domain may
not be available temporarily. It's recommended that you test the update in a separate
test environment before the actual update. The test environment must be
identical to the production environment.

Depending on the system performance, network connection, and installed software,
the update can take anywhere from FIXME minutes to several hours. For large
environments, consult :cite:t:`ucs-performance-guide`.

.. _relnotes-sequence:

Recommended update sequence for environments with more than one UCS system
==========================================================================

In environments with more than one UCS system, take the update sequence of the UCS
systems into account.

The authoritative version of the LDAP directory service operates on the
|UCSPRIMARYDN|, formerly referred to as master domain controller, and replicates
to all the remaining LDAP servers of the UCS domain. As changes to the LDAP
schema can occur during release updates, the |UCSPRIMARYDN| must always be the
first system to be updated during a release update.

.. _relnotes-32bit:

UCS only available for 64 bit
=============================

UCS 5 is only provided for the x86 64 bit architecture (*amd64*).

.. _relnotes-bootloader:

********************************************************
Simultaneous operation of UCS and Debian on UEFI systems
********************************************************

Please note that simultaneous operation of UCS and Debian GNU/Linux on a UEFI
system starting with UCS 5.0 isn't supported.

The reason for this is the GRUB boot loader of |UCSUCS|, which partly uses the
same configuration files as Debian. An already installed Debian leads to the
fact that UCS can't boot (anymore) after the installation of or an update to UCS
5.0. A subsequent installation of Debian results in UCS 5.0 not being able to
boot. For more information, refer to :uv:kb:`17768`.

.. _relnotes-prepare:

*********************
Preparation of update
*********************

This section provides more information you need to consider before you update.

.. _relnotes-sufficient-disc-space:

Sufficient disk space
=====================

Also verify that you have sufficient disk space available for the update. A
standard installation requires a minimum of FIXME GB of disk space. The update
requires approximately FIXME GB additional disk space to download and install the
packages, depending on the size of the existing installation.

.. _relnotes-console-for-update:

Console usage for update
========================

For the update, sign in on the system's local console as user ``root``, and
initiate the update there. Alternatively, you can conduct the update using
|UCSUMC|.

If you want or have to run the update over a network connection, ensure that the
update continues in case of network disconnection. Network connection interrupts
may cancel the update procedure that you initiated over a remote connection. An
interrupted update procedure affects the system severely. To keep the update
running even in case of an interrupted network connection, use tools such as
:command:`tmux`, :command:`screen`, and :command:`at`. All UCS system roles have
these tools installed by default.

.. _relnotes-pre-update-checks:

Script to check for known update issues
=======================================

Univention provides a script that checks for problems which would prevent the
successful update of the system. You can download the script before the update
and run it on the UCS system.

.. code-block:: console

   # download
   $ curl -OOf https://updates.software-univention.de/download/univention-update-checks/pre-update-checks-5.2-0{.gpg,}

   # verify and run script
   $ apt-key verify pre-update-checks-5.2-0{.gpg,} && bash pre-update-checks-5.2-0

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

Following the update, you need to run new or updated join scripts. You can
either use the UMC module *Domain join* or run the command
:command:`univention-run-join-scripts` as user ``root``.

Subsequently, you need to restart the UCS system.

.. _relnotes-packages:

**************************
Notes on selected packages
**************************

The following sections inform about some selected packages regarding the update.

.. _relnotes-usage:

Collection of usage statistics
==============================

When using the *UCS Core Edition*, UCS collects anonymous statistics on the use
of |UCSUMC|. The modules opened get logged to an instance of the web traffic
analysis tool *Matomo*. Usage statistics enable Univention to better tailor the
development of |UCSUMC| to customer needs and carry out usability improvements.

You can verify the license status through the menu entry :menuselection:`License
--> License information` of the user menu in the upper right corner of |UCSUMC|.
Your UCS system is a *UCS Core Edition* system, if the *License information*
lists ``UCS Core Edition`` under *License type*.

UCS doesn't collect usage statistics, when you use an `Enterprise Subscription
<https://www.univention.com/products/prices-and-subscriptions/>`_ license such
as *UCS Base Subscription* or *UCS Standard Subscription*.

Independent of the license used, you can deactivate the usage statistics
collection by setting the |UCSUCRV| :envvar:`umc/web/piwik` to ``false``.

.. _relnotes-browsers:

Recommended browsers for the access to |UCSUMC|
===============================================

|UCSUMC| uses numerous JavaScript and CSS functions to display the web
interface. Your web browser needs to permit cookies. |UCSUMC| requires one of
the following browsers:

* Chrome as of version FIXME

* Firefox as of version FIXME

* Safari and Safari Mobile as of version FIXME

* Microsoft Edge as of version FIXME

Users running older browsers may experience display or performance issues.

.. _relnotes-changelog:

*********
Changelog
*********

You find the changes since UCS 5.0-6 in `Changelog for Univention Corporate Server (UCS) 5.2-0 <../../../changelog/5.2-0/en/index.html>`_.


.. _biblio:

************
Bibliography
************

.. bibliography::

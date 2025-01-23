.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

############################################################################################
Release notes for the installation and update of Univention Corporate Server (UCS) |release|
############################################################################################

Publication date of UCS |release|: 2025-02-05

.. _relnotes-highlights:

******************
Release highlights
******************

With |UCSUCS| 5.2-0, the second minor release for |UCSUCS| (UCS) is available.
It provides several feature improvements and extensions, properties, as well as, bug fixes.
Here is an overview of the most important changes:

* |UCSUCS| 5.2 bases on Debian 12 ``Bookworm`` and therefore it updates a lot of packages.
  As |UCSUCS| 5.0 based on Debian 10 ``Buster``, the intermediate |UCSUCS| 5.1 based on Debian 11 ``Bullseye`` exists.

  |UCSUCS| 5.1 is only required for updating, and **you must never use UCS 5.1 in production**.

  However, the update automatically continues up to 5.2 without the need for manual interaction.
  |UCSUCS| 5.2 provides up-to-date versions for,
  but not limited to,
  the Linux Kernel (6.1.0-28), :program:`Samba` (4.21.1), :program:`OpenLDAP` (2.5.13), PostgreSQL (15), Python (3.11), and Docker (4.18.0).

* :program:`Keycloak` replaces :program:`SimpleSAMLphp` and :program:`Kopano Konnect`.
  In |UCSUCS| 5.2, :program:`Keycloak` is the only Identity Provider (IDP).
  This means that :program:`Keycloak` is the sole component used for authentication and (single-) sign on.
  :program:`Keycloak` is already available as an app for |UCSUCS| 5.0.

  The
  :external+uv-keycloak-mig:doc:`Migration Guide to Keycloak <index>`
  provides information and preparation steps for the update.

  :program:`Keycloak` offers a vast range of features
  and configurability concerning sign-in and usage scenarios,
  such as federation, single-sign on with SAML, OIDC and Kerberos,
  or custom conditional authentication flows.
  For an overview of tested use cases,
  see the
  :external+uv-keycloak-app:doc:`Univention Keycloak app Manual <index>`.

* |UCSUCS| 5.0 supported mixed environments with leading systems updated to 5.0
  while other |UCSUCS| nodes still ran |UCSUCS| 4.
  |UCSUCS| 5.2 drops support for |UCSUCS| 4 environments.
  However, it's still possible to mix |UCSUCS| 5.2 and 5.0 in one domain.

* |UCSUCS| 5.2 updates Python from 3.7 to 3.11.
  While |UCSUCS| 5.0 still supported Python 2.7,
  |UCSUCS| 5.2 no longer supports Python 2.7 and removes its support completely.

* |UCSUCS| 5.2 modernizes the web interface
  and improves the overall look and feel.
  In particular, it improves the integration of various staggered elements
  to make navigation easier and highlight significant areas more prominently.

* The *Univention Configuration Registry (UCR)* now evaluates and validates given values
  according to the configured type to prevent accidental misuse of unsupported values.


.. _relnotes-update:

**********************
Notes about the update
**********************

Prerequisite for updating to UCS 5.2 is that all UCS systems in domain are at
least on version 5.0-9 and that the system intended for update is at least
on version 5.0-9 erratum 1204.

.. important::

   When installing a |UCSBACKUPDN| from the 5.0-9 appliance images or the
   5.0-9 DVD, the final domain join fails,
   if the UCS |UCSPRIMARYDN| has version 5.2-0.

   Start the setup without the domain join
   and upgrade the system to at least 5.0-9 erratum 1204.
   Then start the domain join.
   The upcoming UCS 5.0-10 appliance images and DVD fixes the issue.

Run the update in a maintenance window, because some services in the domain may
not be available temporarily. It's recommended that you test the update in a separate
test environment before the actual update. The test environment must be
identical to the production environment.

Depending on the system performance, network connection, and installed software,
the update can take anywhere from 30 minutes to several hours. For large
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
first system in the update order during a release update.

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

.. _relnotes-keycloak:

Migration of default IDP service before updating to UCS 5.2
===========================================================

Starting with |UCSUCS| 5.2 the :program:`Keycloak` app replaces
:program:`SimpleSAMLphp` and the :program:`Kopano Konnect` app as the default
identity providers in |UCSUCS|. Before the update to UCS 5.2 a manual migration
of the default identity providers is necessary.
You find a detailed description about how
to migrate in
:external+uv-keycloak-mig:doc:`Migration Guide to Keycloak <index>`.

.. _relnotes-openldap-bdb:

Migration of OpenLDAP database backend from BDB to MDB
======================================================

|UCSUCS| 5.2 no longer supports the database backend *Berkeley DB* for :program:`OpenLDAP`.
You need to migrate all systems with the database backend *Berkeley DB*
before the update to UCS 5.2.
For information about how to perform this migration,
see :uv:kb:`22322`.

.. _relnotes-python-311-compatibility:

Mixed environments consisting of both 5.2 and 5.0 nodes
=======================================================

If you continue to operate |UCSREPLICADN|\ s or |UCSMANAGEDNODE|\ s in version 5.0 in your 5.2 domain,
you must ensure that Python 2.7 is no longer used on these systems,
for example in UDM hooks, UMC modules, etc.

If you plan to create a new local software repository on an |UCSUCS| 5.2 system
and want to use this local repository for updating other UCS systems from 5.0-x to 5.2-x,
make sure you read :uv:kb:`23755`
for further notes.

.. _relnotes-mixed-environments:

Python 3.11 compatibility
=========================

Before you update, verify manually crafted Python code for compatibility with
Python 3.11 and adjust it accordingly. This includes |UCSUCR| templates
containing Python code.
Customized AD Connector mapping templates are an example for this.
For advice, see the various Python 3 migration sections in the :cite:t:`developer-reference`.

.. _relnotes-ad-connector-mapping:

AD Connector mapping
====================

When you operate multiple instances of the :program:`AD Connector`
as described in :external+uv-ext-windows:ref:`ad-multiple`,
you need to adjust the mapping configuration
and ensure Python 3.11 compatibility before the update.
:uv:kb:`17754` describes the steps.

.. _relnotes-sufficient-disc-space:

Sufficient disk space
=====================

Also verify that you have sufficient disk space available for the update. A
standard installation requires a minimum of 6-10 GB of disk space. The update
requires approximately 5 GB additional disk space to download and install the
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

Please verify the PostgreSQL version on all UCS systems that updated to UCS 5.2.
As UCS 5.2 ships Version 15 of PostgreSQL, updated systems may need
migration from PostgreSQL 11.
For the recommended migration steps,
see :uv:kb:`22162`.

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

* Chrome as of version 131

* Firefox as of version 128

* Safari and Safari Mobile as of version 18

* Microsoft Edge as of version 128

Users running older browsers may experience display or performance issues.

.. _relnotes-changelog:

*********
Changelog
*********

You find the changes since UCS 5.0-9 in
:external+uv-changelog-5.2-0:doc:`index`.

.. _biblio:

************
Bibliography
************

.. bibliography::

############################################################################################
Release notes for the installation and update of Univention Corporate Server (UCS) |release|
############################################################################################

Publication date of UCS |release|: 2023-02-07

.. _relnotes-highlights:

******************
Release Highlights
******************

With |UCSUCS| 5.0-3, the third point release for |UCSUCS| (UCS) 5.0 is now
available. It provides several feature improvements and extensions, new
properties as well as various improvements and bug fixes. Here is an overview of
the most important changes:

* The program :program:`univention-support-info` is now included with the
  distribution. It can be used to collect useful information from the system
  when a support case is opened with Univention GmbH.

* Several new modules have been added to the UMC module :guilabel:`System
  diagnostic` and some existing ones have been improved. For example several
  |UCSUCRV|\ s now have type information, which can be used to validate their
  values. Individual modules can also be disabled in case of false positives.

* Group membership is now maintained using the OpenLDAP overlay module
  ``memberof``, which improves performance in large environments.

* Operational LDAP attributes can now be visualized in the :guilabel:`Directory Manager`.

* The program :program:`univention-keycloak` was added to support the new App
  :guilabel:`Keycloak`, which can be installed from the :guilabel:`App Center`
  to provide Single Sign On.

* This |UCSUCS| release is based on Debian 10.13 Buster.

* The Linux kernel has been updated to version 5.10.162 from Debian 11.6
  Bullseye to support newer hardware.

* Various security updates have been integrated into UCS 5.0-3, for example for
  :program:`Samba4`, Squid, BIND9, PostgreSQL and Dovecot.

.. _relnotes-update:

**********************
Notes about the update
**********************

During the update some services in the domain may not be available temporarily,
that is why the update should occur in a maintenance window. It is recommended
to test the update in a separate test environment prior to the actual update.
The test environment should be identical to the production environment.
Depending on the system performance, network connection and the installed
software the update will take between 20 minutes and several hours. In large
environments it may be useful to consult :cite:t:`ucs-performance-guide`.

.. _relnotes-order:

Recommended update order for environments with more than one UCS server
=======================================================================

In environments with more than one UCS system, the update order of the UCS
systems must be borne in mind:

The authoritative version of the LDAP directory service is maintained on the
|UCSPRIMARYDN| (formerly referred to as master domain controller) and replicated
to all the remaining LDAP servers of the UCS domain. As changes to the LDAP
schema can occur during release updates, the |UCSPRIMARYDN| must always be the
first system to be updated during a release update.

.. _relnotes-32bit:

UCS only available for 64 bit
=============================

UCS 5 is only provided for the x86 64 bit architecture (*amd64*). Existing 32
bit UCS systems cannot be updated to UCS 5.

.. _relnotes-bootloader:

********************************************************
Simultaneous operation of UCS and Debian on UEFI systems
********************************************************

Please note that simultaneous operation of UCS and Debian on a UEFI system
starting with UCS 5.0 is not supported.

The reason for this is the GRUB boot loader of |UCSUCS|, which partly uses the
same configuration files as Debian. An already installed Debian leads to the
fact that UCS cannot be booted (any more) after the installation of or an update
to UCS 5.0. A subsequent installation of Debian will also result in UCS 5.0 not
being able to boot.

At the following help article further hints to this topic are collected:
:uv:kb:`17768`.

.. _relnotes-localrepo:

************************
Local package repository
************************

This section is relevant for environments where a :external+uv-manual:ref:`local
repository <software-create-repo>` is set up. The installed (major) version of
UCS determines which packages a local repository provides. A repository running
on a UCS server with version 4.x will only provide packages up to UCS 4.x, a
repository server running on UCS 5 will only provide packages for UCS 5 and
newer versions. To upgrade systems to UCS 5 in an environment with a local
repository, the following are some of the options. First, a local UCS 5
repository server must be set up.

* A new UCS 5 system is installed as a |UCSPRIMARYDN| from the DVD or from a
  virtualized base image. Then :external+uv-manual:ref:`a local repository is
  set up on this system <software-create-repo>` as described in
  :cite:t:`ucs-manual`.

* A new UCS 5 system is installed with the system role |UCSBACKUPDN|,
  |UCSREPLICADN| or |UCSMANAGEDNODE| from the DVD or from a virtualized base
  image. In system setup, select that the system will not join a domain. Then
  :external+uv-manual:ref:`set up a local repository on this system
  <software-create-repo>` as described in :cite:t:`ucs-manual`. After the
  |UCSPRIMARYDN| used in the domain is upgraded to UCS 5, the UCS 5 repository
  server can join the domain via :command:`univention-join`.

To upgrade a system in the domain to UCS 5, the server should first be upgraded
to the latest package level available for UCS 4.x. Then the repository server
used by the system is switched to the local UCS 5 repository by changing the
|UCSUCRV| :external+uv-manual:envvar:`repository/online/server`. The system can
now be upgraded to UCS 5 via the |UCSUMC| or via the command line.

.. _relnotes-prepare:

*********************
Preparation of update
*********************

Manually crafted Python code needs to be checked for compatibility with Python
3.7 before the Update and adjusted accordingly. This includes |UCSUCR| templates
containing Python code. Customized AD-Connector mapping templates are an example
for this. See also the :cite:t:`developer-reference` for advice.

When multiple instances of the :program:`AD Connector` are operated as described
in :ref:`ad-multiple`, an
adjustment of the mapping configuration is needed and Python 3.7 compatibility
must be ensured before the update. :uv:kb:`17754` describes the steps.

It must be checked whether sufficient disk space is available. A standard
installation requires a minimum of 6-10 GB of disk space. The update requires
approximately 1-2 GB additional disk space to download and install the packages,
depending on the size of the existing installation.

For the update, a login should be performed on the system's local console as
user ``root``, and the update should be initiated there. Alternatively, the
update can be conducted using |UCSUMC|.

Remote updating via SSH is not recommended as this may result in the update
procedure being canceled, e.g., if the network connection is interrupted. In
consequence, this can affect the system severely. If updating should occur over
a network connection nevertheless, it must be verified that the update continues
in case of disconnection from the network. This can be achieved, e.g., using the
tools :command:`tmux`, :command:`screen` and :command:`at`. These tools are
installed on all UCS system roles by default.

Univention provides a script that checks for problems which would prevent the
successful update of the system. Prior to the update, this script can be
downloaded and executed on the UCS system.

.. code-block:: console

   # download
   $ curl -OOf https://updates.software-univention.de/download/univention-update-checks/pre-update-checks-5.0-3{.gpg,}

   # verify and run script
   $ apt-key verify pre-update-checks-5.0-3{.gpg,} && bash pre-update-checks-5.0-3

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

Following the update, new or updated join scripts need to be executed. This can
be done in two ways: Either using the UMC module *Domain join* or by running the
command :command:`univention-run-join-scripts` as user ``root``.

Subsequently the UCS system needs to be restarted.

.. _relnotes-packages:

**************************
Notes on selected packages
**************************

.. _relnotes-usage:

Collection of usage statistics
==============================

Anonymous usage statistics on the use of |UCSUMC| are collected when using the
*UCS Core Edition*. The modules opened get logged to an instance of the web
traffic analysis tool *Matomo*. This makes it possible for Univention to tailor the
development of |UCSUMC| better to customer needs and carry out usability
improvements.

This logging is only performed when the *UCS Core Edition* license is used. The
license status can be verified via the menu entry :menuselection:`License -->
License information` of the user menu in the upper right corner of |UCSUMC|. If
``UCS Core Edition`` is listed under *License type*, this version is in use.
When a regular UCS license is used, no usage statistics are collected.

Independent of the license used, the statistics generation can be deactivated by
setting the |UCSUCRV| :envvar:`umc/web/piwik` to *false*.

.. _relnotes-browsers:

Recommended browsers for the access to |UCSUMC|
===============================================

|UCSUMC| uses numerous JavaScript and CSS functions to display the web
interface. Cookies need to be permitted in the browser. The following browsers
are recommended:

* Chrome as of version 85

* Firefox as of version 78

* Safari and Safari Mobile as of version 13

* Microsoft Edge as of version 88

Users running older browsers may experience display or performance issues.

.. _relnotes-changelog:

*********
Changelog
*********

You find the changes since UCS 5.0-2 in
:external+uv-changelog:doc:`index`.


.. _biblio:

************
Bibliography
************

.. bibliography::

.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _relnotes-changelog:

#########################################################
Changelog for Univention Corporate Server (UCS) |release|
#########################################################

.. Temporary hack until they are merged
.. include:: temp.rst

**************************
* Notes about the update *
**************************

Prerequisite for updating is at least UCS TODO

Migration of default IDP service before updating to UCS 5.2
-----------------------------------------------------------

Starting with |UCS| 5.2 the :program:`Keycloak` app replaces
:program:`SimpleSAMLphp` and the :program:`Kopano Konnect` app as the default
identity providers in |UCS|. Before the update to UCS 5.2 an manual migration
of the default identity providers is necessary. A detailed description of how
to migrate can be found in https://docs.software-univention.de/keycloak-migration/index.html.


Migration of OpenLDAP database backend from BDB to MDB
------------------------------------------------------

|UCS| 5.2 will no longer support the :program:`Berkeley DB` database back-end
for :program:`OpenLDAP`. All system with :program:`Berkeley DB` as database
back-end have to be migrated before the update to UCS 5.2. Please see
https://help.univention.com/t/22322 for how to perform this migration.

*************************
* Preparation of update *
*************************

* Univention provides a script that checks for problems which would prevent the
  successful update of the system. Prior to the update, this script can be
  downloaded and executed on the UCS system.

  .. code-block:: bash
     :caption: Run update check script
     :name: run-update-check-script

     # download
     curl -OOf https://updates.software-univention.de/download/univention-update-checks/pre-update-checks-5.2-0{.gpg,}

     # verify and run script
     apt-key verify pre-update-checks-5.2-0{.gpg,} && bash pre-update-checks-5.2-0
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

.. _changelog-general:

*******
General
*******

.. _security:

* All security updates issued for UCS 5.0-6 are included:

.. _debian:

* The following updated packages from Debian 10.13 are included:

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-portal:

Univention Portal
=================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-server:

Univention Management Console server
====================================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-appcenter:

Univention App Center
=====================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-udmcli:

|UCSUDM| and command line interface
===================================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-join:

Domain join module
==================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-ucr:

Univention Configuration Registry module
========================================

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-other:

Other modules
=============

* FIXME (:uv:bug:`99999`)

.. _changelog-umc-development:

Development of modules for |UCSUMC|
===================================

* FIXME (:uv:bug:`99999`)

.. _changelog-lib:

Univention base libraries
=========================

* FIXME (:uv:bug:`99999`)

.. _changelog-service-saml:

SAML
====

* FIXME (:uv:bug:`99999`)

.. _changelog-service-selfservice:

Univention self service
=======================

* FIXME (:uv:bug:`99999`)

.. _changelog-service-mail:

Mail services
=============

* FIXME (:uv:bug:`99999`)

.. _changelog-service-virus:

Spam/virus detection and countermeasures
========================================

* FIXME (:uv:bug:`99999`)

.. _changelog-service-nagios:

Nagios
======

* FIXME (:uv:bug:`99999`)

.. _changelog-service-radius:

RADIUS
======

* FIXME (:uv:bug:`99999`)

.. _changelog-service-pam:

PAM / Local group cache
=======================

* FIXME (:uv:bug:`99999`)

.. _changelog-win-samba:

Samba
=====

* FIXME (:uv:bug:`99999`)

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* FIXME (:uv:bug:`99999`)

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* FIXME (:uv:bug:`99999`)

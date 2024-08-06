.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _relnotes-changelog:

#########################################################
Changelog for Univention Corporate Server (UCS) |release|
#########################################################

.. _changelog-general:

*******
General
*******

* The version of all modified join scripts has been increased by 10 so that join
  script versions in UCS 5.0-x can be increased after UCS 5.1 has been released
  (:uv:bug:`56927`).

* All Python 2.7 packages have been removed (:uv:bug:`56533`, :uv:bug:`56533`,
  :uv:bug:`55994`).

* The code compatibility for Python 3.11 has been improved (:uv:bug:`55915`).

* The package management library of :program:`univention-lib` has been adjusted to
  upstream changes in :program:`apt` (:uv:bug:`56536`).

* Code which ensured compatibility with Python 2.7 has been removed
  (:uv:bug:`56604`).

* Various dependencies on old transitional Debian and Univention packages have been
  replaced with dependencies on new successor packages. The :program:`univention-saml`
  packages were transitional since UCS 5.1 and have now been removed completely
  (:uv:bug:`56858`).

* The argument to the ``--ucsversionstart`` flag for
  ``ucs_registerLDAPExtension`` has been changed to 5.0-7 (:uv:bug:`56124`).

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

* Strict type checking has been enabled when setting or modifying |UCSUCRV|\ s
  (:uv:bug:`55981`).

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* The deprecated SSH configuration option ``ChallengeResponseAuthentication``
  has been replaced with ``KbdInteractiveAuthentication``. The new |UCSUCRV|
  :envvar:`sshd/KbdInteractiveAuthentication` allows to configure this option
  (:uv:bug:`56147`).

* Scripts have been adjusted for binary paths changed in Debian
  (:uv:bug:`56665`).

* Various Univention Configuration Registry templates have been updated to
  closer match upstream Debian 12 configuration. The |UCSUCRV|
  :envvar:`syslog/template/default` has been deleted. The template files
  :file:`/etc/default/samba` and :file:`/etc/default/apache2` have been deleted
  (:uv:bug:`46120`).

* The package :program:`ntp` has been replaced by the package :program:`ntpsec`
  (:uv:bug:`56661`).

.. _changelog-basis-other:

Other system services
=====================

* :program:`univention-ssh` has been adjusted to work with ``openssh-8.4-p1``
  (:uv:bug:`56593`).

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-domain-openldap:

OpenLDAP
========

* The configurability of the LDAP overlay module ``memberOf`` has been removed.
  Since UCS 4.3 the default settings are required (:uv:bug:`56662`).

* All LDAP utility command line calls have been adjusted to use :samp:`-H
  {LDAP_URI}` instead of the obsolete :samp:`-h {host} -p {port}` arguments
  (:uv:bug:`55997`).

* Support for the :program:`Berkeley DB` database backend for
  :program:`OpenLDAP` has been removed (:uv:bug:`57112`).

* The Univention Virtual Machine Manager related LDAP schema and contents are
  required to be removed before upgrading to UCS 5.2 (:uv:bug:`56651`).

.. _changelog-domain-openldap-schema:

LDAP schema changes
-------------------

* The LDAP attributes ``univentionFetchmailAddress``,
  ``univentionFetchmailServer``, ``univentionFetchmailProtocol``,
  ``univentionFetchmailPasswd``, ``univentionFetchmailKeepMailOnServer`` and
  ``univentionFetchmailUseSSL`` are deprecated, ``univentionFetchmailSingle`` is
  used instead for Fetchmail configurations (:uv:bug:`55905`).

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* Listener modules are now executed with Python 3.11 (:uv:bug:`56533`).

.. _changelog-domain-dnsserver:

DNS server
==========

* All :program:`systemd` references for the renamed ``named.service`` have been
  adjusted (:uv:bug:`56003`).

.. _changelog-udm:

LDAP Directory Manager
======================

* The HTTP status code for move operations has been fixed (:uv:bug:`55057`).

* The obsolete UDM modules ``settings/portal*`` have been removed
  (:uv:bug:`52048`).

* The list of country names for the UDM syntax class ``Country`` has been
  updated (:uv:bug:`56541`).

* Moving of objects without children is now done directly and doesn't require a
  HTTP redirection (:uv:bug:`55019`).

* A migration of the LDAP data for the mapping of the UDM property ``country``
  to the LDAP attribute ``c`` is now enforced for the upgrade to UCS 5.2
  (:uv:bug:`56528`).

* The default values of |UCSUCRV| :envvar:`directory/manager/user/enable-legacy-
  username-format` and |UCSUCRV| :envvar:`directory/manager/group/enable-legacy-
  cn-format` have been changed to ``false`` which configures UCS to disallow
  purely numerical user and group names (:uv:bug:`56992`).

* The |UCSUCRV| :envvar:`directory/manager/user/group-memberships-via-memberof`
  has been removed. Group memberships in the UDM module ``users/user`` are now
  always resolved via the LDAP attribute ``memberOf`` (:uv:bug:`56253`).

.. _changelog-service-keycloak:

Keycloak
========

* Several changes to ``univention-keycloak`` for better integration with
  Univention Nubus (:uv:bug:`57492`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

* Deprecated Python APIs especially regarding the use of :program:`python-
  notifier` have been removed (:uv:bug:`56538`).

.. _changelog-umc-portal:

Univention Portal
=================

* The UCS Portal's graphical user interface has received various updates
  (:uv:bug:`57083`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* Removed the commands :command:`univention-rename-app` and :command
  :`univention-register-apps` which used old code that did not work since at
  least UCS 5.0 and which are unneeded (:uv:bug:`56724`).

* The initial App Center cache has been updated. It is important especially when
  working offline (:uv:bug:`56716`).

* Adapted code to API changes in the new Python :program:`apt` library
  (:uv:bug:`56598`).

* The App Center now avoids assigning a subnet to an app that conflicts with
  other networks already created in docker (:uv:bug:`57210`).

.. _changelog-umc-user:

User management
===============

* The old self service frontend (``/univention/self-service/``) has been removed
  (:uv:bug:`56601`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* The diagnostic script :file:`62_check_slapschema` has been adjusted to changed
  output of :program:`slapschema` (:uv:bug:`56546`).

* Added diagnostic script :file:`68_old_fetchmail_attributes` to detect the use
  of deprecated Fetchmail LDAP attributes (:uv:bug:`55905`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* The package dependencies have been adjusted to depend on
  :program:`libldap-2.5-0` (:uv:bug:`56596`).

* The concept ``decode ignorelist`` has been removed. UDM does not decode
  attributes automatically anymore since UCS 5.0 (:uv:bug:`50343`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* During the update to UCS 5.2, objects from deprecated UCS versions are deleted
  from the LDAP directory. Information about deleted objects and the objects
  LDIF output can be found in the logfile :file:`/var/univention-backup/update-
  to-5.2-0/removed_with_ucs5_*timestamp*.ldif` (:uv:bug:`56134`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-postgresql:

PostgreSQL
==========

* PostgreSQL has been upgraded to version 15. Password encryption from ``md5``
  to ``scram-sha-256`` can now be achieved by using the UCR variables |UCSUCRV|
  :envvar:`postgres15/password-encryption` and |UCSUCRV|
  :envvar:`postgres15/pg_hba/password-encryption` (:uv:bug:`56540`).

.. _changelog-service-mail:

Mail services
=============

* Hide deprecated Fetchmail LDAP attributes in UMC - Improved script
  :file:`/usr/share/univention-fetchmail/migrate-fetchmail.py` - Run migration
  script on upgrade (:uv:bug:`55905`).

.. _changelog-service-imap:

IMAP services
-------------

* The |UCSUCRV| :envvar:`mail/dovecot/ssl/protocols` has been replaced with
  |UCSUCRV| :envvar:`mail/dovecot/ssl/min_protocol` and must manually be set.
  The minimum required TLS version has been adjusted to TLS 1.2. The TLS
  versions 1.0 and 1.1 are no longer supported with default settings
  (:uv:bug:`56544`).

.. _changelog-service-print:

Printing services
=================

* The printer driver list has been updated (:uv:bug:`56542`).

.. _changelog-service-nagios:

Nagios
======

* The Nagios server functionality has been removed from UDM. Therefore the UDM
  module ``nagios/timeperiod`` has been removed. The UDM module
  ``nagios/service`` has been reduced to the minimal required NRPE properties
  (:uv:bug:`56367`).

* LDAP credentials are now passes via the environment variable
  :envvar:`LDAP_PASSWORD` instead of using the deprecated option ``-y``
  (:uv:bug:`56580`).

* The patches to :program:`monitoring-plugins` have been adapted to the new
  upstream version. The patch adding the option ``-y`` to read the LDAP
  credentials from a file has been dropped. The patch fixing a spelling mistake
  has been dropped as it has been fixed upstream (:uv:bug:`55829`).

.. _changelog-service-radius:

RADIUS
======

* FreeRADIUS now uses TLS 1.3 as default maximum TLS version. TLS 1.3 may cause
  issues for Microsoft Windows 10 Clients. See UCS Manual (:uv:bug:`55763`).

* The MD4 functionality is now provided by the ``python3-samba`` package because
  it was dropped from ``OpenSSL`` (:uv:bug:`55996`).

* The FreeRADIUS service now uses a specific credentials file in
  :file:`/etc/freeradius.secret` (:uv:bug:`55963`).

.. _changelog-service-ssl:

SSL/TLS
=======

* Radius now has TLS 1.3 enabled by default. TLS 1.3 might cause issues with
  Microsoft Windows 10. To use TLS 1.2, set the |UCSUCRV|
  :envvar:`freeradius/conf/tls-max-version` to the value ``1.2``
  (:uv:bug:`55763`).

.. _changelog-service-dhcp:

DHCP services
=============

* The LDAP configuration in :file:`dhcpd.conf` has been disabled temporarily
  during UCS 5.1 to avoid issues with :program:`isc-dhcp-server` version
  ``4.4.1-2.3`` running into a thread deadlock when testing the configuration
  (:uv:bug:`56730`).

.. _changelog-service-pam:

PAM / Local group cache
=======================

* The deprecated :program:`libnss-ldap` and :program:`libpam-ldap` have been replaced with
  :program:`sssd`. :program:`sssd` is currently used for users only. This also means that
  :program:`nscd` is not used any longer for the :program:`passwd` related system calls (but
  it still is used as cache for ``hosts`` resolution). The UCR variables
  :envvar:`nscd/passwd/.` are not used any longer. The :program:`sssd` is configured via
  :file:`/etc/sssd/sssd.conf` which is generated from a UCR template now. :program:`sssd`
  additionally reads configuration sub files from the directory
  :file:`/etc/sssd/conf.d`, which can be used in case options need to be customized
  differently from what the UCR template initially supports.
  The user cache of :program:`sssd` can be flushed by running ``sss_cache -U``, instead
  of running ``nscd -i passwd``. Please note that :program:`sssd` by default doesn't
  dynamically ``enumerate`` accounts in :program:`passwd`. Some tools that expect that by
  default, may need adjustment to consider this; for example ``repquota`` needs to be called
  with the option ``-C`` to resolve ``uid`` numbers to names. Additionally
  :program:`sssd` doesn't support resolving ``shadow`` information at all, so e.g.
  ``pam_unix`` will not be able to read ``shadow`` related info for domain users
  (so there's a difference between domain users managed in UDM/LDAP and
  traditional Linux local accounts). Please also note that UCS currently still
  uses ``pam_krb5`` separately from :program:`sssd`, as UCS and Samba use Heimdal
  Kerberos, while :program:`sssd` may be more leaning towards MIT Kerberos. We want to
  avoid hard to detect compatibility issues here, currently (:uv:bug:`56793`).

* The obsolete :program:`pam-tally` has been replaced with :program:`pam-faillock`
  (:uv:bug:`56547`).

* The obsolete :program:`libpam-cracklib` has been replaced with :program:`libpam-pwquality`
  (:uv:bug:`56002`).

* The :program:`pam` configuration file :file:`/etc/pam.d/common-session-noninteractive` is now
  generated from a UCR template (:uv:bug:`57298`).

.. _changelog-service-nfs:

NFS
===

* The :program:`systemd` service unit for :program:`nfs-kernel-server` has been
  adjusted to make restarts possible again (:uv:bug:`56545`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* The default for the Samba database is now ``mdb`` (:uv:bug:`57145`).


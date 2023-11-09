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

* The dependency of :command:`univention-fix-ucr-dns` on :program:`py3dns` has been replaced by
  :program:`dnspython` to support EDNS, which is required for virtual machines on AWS-
  EC2 and OpenStack. This also fixes an issue with "Amazon Provided DNS", which
  only supports "recursive queries": as such they were not identified as
  forwarding DNS services and did not get moved from |UCSUCRV|\ s
  :envvar:`nameserver[123]` to :envvar:`dns/forwarder[123]`. This resulted in UCS domain
  specific queries being sent wrongly to the "Amazon Provided DNS", which then
  were not able to answer them and returned a failure instead, leading to all
  kind of application errors (:uv:bug:`56911`).

.. _security:

* All security updates issued for UCS 5.0-6 are included:

  * :program:`bind9` (:uv:cve:`2023-3341`) (:uv:bug:`57029`)

  * :program:`bluez` (:uv:cve:`2023-45866`) (:uv:bug:`56921`)

  * :program:`curl` (:uv:cve:`2023-28322`, :uv:cve:`2023-46218`)
    (:uv:bug:`56941`)

  * :program:`exim4` (:uv:cve:`2023-51766`) (:uv:bug:`56968`)

  * :program:`firefox-esr` (:uv:cve:`2023-6856`, :uv:cve:`2023-6857`,
    :uv:cve:`2023-6858`, :uv:cve:`2023-6859`, :uv:cve:`2023-6860`,
    :uv:cve:`2023-6861`, :uv:cve:`2023-6862`, :uv:cve:`2023-6863`,
    :uv:cve:`2023-6864`, :uv:cve:`2023-6865`, :uv:cve:`2023-6867`,
    :uv:cve:`2024-0741`, :uv:cve:`2024-0742`, :uv:cve:`2024-0746`,
    :uv:cve:`2024-0747`, :uv:cve:`2024-0749`, :uv:cve:`2024-0750`,
    :uv:cve:`2024-0751`, :uv:cve:`2024-0753`, :uv:cve:`2024-0755`,
    :uv:cve:`2024-1546`, :uv:cve:`2024-1547`, :uv:cve:`2024-1548`,
    :uv:cve:`2024-1549`, :uv:cve:`2024-1550`, :uv:cve:`2024-1551`,
    :uv:cve:`2024-1552`, :uv:cve:`2024-1553`) (:uv:bug:`56939`,
    :uv:bug:`57008`, :uv:bug:`57085`)

  * :program:`gnutls28` (:uv:cve:`2024-0553`) (:uv:bug:`57086`)

  * :program:`imagemagick` (:uv:cve:`2023-1289`, :uv:cve:`2023-34151`,
    :uv:cve:`2023-39978`, :uv:cve:`2023-5341`) (:uv:bug:`57080`)

  * :program:`intel-microcode` (:uv:cve:`2023-23583`)
    (:uv:bug:`56920`)

  * :program:`jinja2` (:uv:cve:`2024-22195`) (:uv:bug:`57007`)

  * :program:`libde265` (:uv:cve:`2023-49465`, :uv:cve:`2023-49467`,
    :uv:cve:`2023-49468`) (:uv:bug:`56948`)

  * :program:`linux` (:uv:cve:`2021-44879`, :uv:cve:`2023-0590`,
    :uv:cve:`2023-1077`, :uv:cve:`2023-1206`, :uv:cve:`2023-1989`,
    :uv:cve:`2023-25775`, :uv:cve:`2023-3212`, :uv:cve:`2023-3390`,
    :uv:cve:`2023-34319`, :uv:cve:`2023-34324`, :uv:cve:`2023-35001`,
    :uv:cve:`2023-3609`, :uv:cve:`2023-3611`, :uv:cve:`2023-3772`,
    :uv:cve:`2023-3776`, :uv:cve:`2023-39189`, :uv:cve:`2023-39192`,
    :uv:cve:`2023-39193`, :uv:cve:`2023-39194`, :uv:cve:`2023-40283`,
    :uv:cve:`2023-4206`, :uv:cve:`2023-4207`, :uv:cve:`2023-4208`,
    :uv:cve:`2023-4244`, :uv:cve:`2023-42753`, :uv:cve:`2023-42754`,
    :uv:cve:`2023-42755`, :uv:cve:`2023-45863`, :uv:cve:`2023-45871`,
    :uv:cve:`2023-4622`, :uv:cve:`2023-4623`, :uv:cve:`2023-4921`,
    :uv:cve:`2023-51780`, :uv:cve:`2023-51781`, :uv:cve:`2023-51782`,
    :uv:cve:`2023-5717`, :uv:cve:`2023-6606`, :uv:cve:`2023-6931`,
    :uv:cve:`2023-6932`) (:uv:bug:`56972`)

  * :program:`linux-latest` (:uv:cve:`2021-44879`,
    :uv:cve:`2023-0590`, :uv:cve:`2023-1077`, :uv:cve:`2023-1206`,
    :uv:cve:`2023-1989`, :uv:cve:`2023-25775`, :uv:cve:`2023-3212`,
    :uv:cve:`2023-3390`, :uv:cve:`2023-34319`, :uv:cve:`2023-34324`,
    :uv:cve:`2023-35001`, :uv:cve:`2023-3609`, :uv:cve:`2023-3611`,
    :uv:cve:`2023-3772`, :uv:cve:`2023-3776`, :uv:cve:`2023-39189`,
    :uv:cve:`2023-39192`, :uv:cve:`2023-39193`, :uv:cve:`2023-39194`,
    :uv:cve:`2023-40283`, :uv:cve:`2023-4206`, :uv:cve:`2023-4207`,
    :uv:cve:`2023-4208`, :uv:cve:`2023-4244`, :uv:cve:`2023-42753`,
    :uv:cve:`2023-42754`, :uv:cve:`2023-42755`, :uv:cve:`2023-45863`,
    :uv:cve:`2023-45871`, :uv:cve:`2023-4622`, :uv:cve:`2023-4623`,
    :uv:cve:`2023-4921`, :uv:cve:`2023-51780`, :uv:cve:`2023-51781`,
    :uv:cve:`2023-51782`, :uv:cve:`2023-5717`, :uv:cve:`2023-6606`,
    :uv:cve:`2023-6931`, :uv:cve:`2023-6932`) (:uv:bug:`56972`)

  * :program:`linux-signed-amd64` (:uv:cve:`2021-44879`,
    :uv:cve:`2023-0590`, :uv:cve:`2023-1077`, :uv:cve:`2023-1206`,
    :uv:cve:`2023-1989`, :uv:cve:`2023-25775`, :uv:cve:`2023-3212`,
    :uv:cve:`2023-3390`, :uv:cve:`2023-34319`, :uv:cve:`2023-34324`,
    :uv:cve:`2023-35001`, :uv:cve:`2023-3609`, :uv:cve:`2023-3611`,
    :uv:cve:`2023-3772`, :uv:cve:`2023-3776`, :uv:cve:`2023-39189`,
    :uv:cve:`2023-39192`, :uv:cve:`2023-39193`, :uv:cve:`2023-39194`,
    :uv:cve:`2023-40283`, :uv:cve:`2023-4206`, :uv:cve:`2023-4207`,
    :uv:cve:`2023-4208`, :uv:cve:`2023-4244`, :uv:cve:`2023-42753`,
    :uv:cve:`2023-42754`, :uv:cve:`2023-42755`, :uv:cve:`2023-45863`,
    :uv:cve:`2023-45871`, :uv:cve:`2023-4622`, :uv:cve:`2023-4623`,
    :uv:cve:`2023-4921`, :uv:cve:`2023-51780`, :uv:cve:`2023-51781`,
    :uv:cve:`2023-51782`, :uv:cve:`2023-5717`, :uv:cve:`2023-6606`,
    :uv:cve:`2023-6931`, :uv:cve:`2023-6932`) (:uv:bug:`56972`)

  * :program:`mariadb-10.3` (:uv:cve:`2023-22084`) (:uv:bug:`57005`)

  * :program:`openjdk-11` (:uv:cve:`2024-20918`, :uv:cve:`2024-20919`,
    :uv:cve:`2024-20921`, :uv:cve:`2024-20926`, :uv:cve:`2024-20945`,
    :uv:cve:`2024-20952`) (:uv:bug:`57010`)

  * :program:`openssh` (:uv:cve:`2021-41617`, :uv:cve:`2023-48795`,
    :uv:cve:`2023-51385`) (:uv:bug:`56940`)

  * :program:`pillow` (:uv:cve:`2023-50447`) (:uv:bug:`57032`)

  * :program:`postfix` (:uv:cve:`2023-51764`) (:uv:bug:`57030`)

  * :program:`squid` (:uv:cve:`2023-46728`, :uv:cve:`2023-46846`,
    :uv:cve:`2023-46847`, :uv:cve:`2023-49285`, :uv:cve:`2023-49286`,
    :uv:cve:`2023-50269`) (:uv:bug:`56964`, :uv:bug:`57009`)

  * :program:`sudo` (:uv:cve:`2023-28486`, :uv:cve:`2023-28487`,
    :uv:cve:`2023-7090`) (:uv:bug:`57031`)

  * :program:`unbound` (:uv:cve:`2023-50387`, :uv:cve:`2023-50868`)
    (:uv:bug:`57081`)

  * :program:`univention-mail-postfix` (:uv:cve:`2023-51764`)
    (:uv:bug:`56957`)

  * :program:`wpa` (:uv:cve:`2023-52160`) (:uv:bug:`57108`)

  * :program:`xorg-server` (:uv:cve:`2023-6377`, :uv:cve:`2023-6478`,
    :uv:cve:`2023-6816`, :uv:cve:`2024-0229`, :uv:cve:`2024-21885`,
    :uv:cve:`2024-21886`) (:uv:bug:`56923`, :uv:bug:`57006`)


.. _debian:

* The following updated packages from Debian 0.0 are included:

  :program:`FIXME`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

  :program:`orcania` (:uv:bug:`49006`), :program:`rhonabwy`
  (:uv:bug:`49006`), :program:`ulfius` (:uv:bug:`49006`),
  :program:`yder` (:uv:bug:`49006`)

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

* Fix traceback when :py:class:`Interfaces()` is used with :py:class:`ReadOnlyConfigRegistry()`
  (:uv:bug:`56911`).

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-domain-openldap:

OpenLDAP
========

* During normal replication objects with ``objectClass=lock`` are not replicated.
  But during initial join they were. By adjusting the filter in the listener
  module this is now avoided, speeding up initial replication
  (:uv:bug:`56954`).

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* During normal replication objects with ``objectClass=lock`` are not replicated.
  But during initial join they were. By adjusting the filter in the listener
  module this is now avoided, speeding up initial replication
  (:uv:bug:`56954`).

* In case the communication to the notifier fails, e.g. due to a restart of the
  |UCSUDN| service on the UCS Primary Directory Node, the
  listener did not retry but exit and relies on :program:`systemd` to get restarted. This
  strategy does not work during the initialization phase while joining, when
  the listener is not yet run as :program:`systemd` service. A retry mechanism has been
  introduced for this case, which is similar to what we already did for the
  connection to the LDAP server. There is a new |UCSUCRV|
  :envvar:`listener/notifier/retries` with default 30. There is an exponential back-off
  algorithm to delay the retries and log messages are generated showing what is
  going on (:uv:bug:`57024`).

.. _changelog-domain-dnsserver:

DNS server
==========

* DNS zones are now detected by having a ``SOA`` record instead of having a
  relative name ``@``. This is allowed as DNS labels might consist of any 8-bit
  octets including an escaped ``\@``. Deleting such entries resulted into the
  complete zone being dropped from BIND9 (:uv:bug:`50385`).

* The listener module writing the :program:`BIND9` configuration files now ignores DNS
  zone files with invalid file names (:uv:bug:`57013`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* For enhanced automated testing the UDM REST API now handles requests with
  ``application/json-patch+json`` mime type (:uv:bug:`55555`).

* The UDM REST API now supports authentication via the ``Bearer`` authentication
  scheme (:uv:bug:`49006`).

* UDM REST now supports a different LDAP base for each |UCSUDM| module. This is a
  requirement for the blocklist feature (:uv:bug:`57039`).

* After log rotating log files of the UDM REST API, the service is reloaded so
  that it logs into the new files (:uv:bug:`54338`).

* All |UCSUDM| log lines are now prefixed with the request ID. This can be disabled
  via the |UCSUCRV| :envvar:`directory/manager/rest/debug/prefix-with-request-id`
  (:uv:bug:`56970`).

* For containerized environments, the UDM REST API OpenAPI Schema user
  interface is now exposed via the UDM REST API server as well
  (:uv:bug:`57058`).

* The replacement of the fallback |UCSUMC| logger has been adjusted to use
  :program:`univention.logging` (:uv:bug:`55324`).

.. _changelog-umc-portal:

Univention Portal
=================

* The HTML title and icon of the Portal is now configurable via the |UCSUCRV|\ s
  :envvar:`umc/web/title` and :envvar:`umc/web/favicon` (:uv:bug:`56917`).

* The labels of the self-service password forgotten form were always displayed
  in English when they were accessed directly via URL without navigating
  through the portal (:uv:bug:`56853`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* The custom :py:mod:`univention.debug` wrapper of |UCSUMC| has been replaced by the new
  logging interface :py:mod:`univention.logging` (:uv:bug:`55324`).

* The |UCSUCRV| :envvar:`ldap/server/sasl/mech_list` has been added to allow
  restricting the list of SASL mechanisms that the local LDAP server offers. By
  default GSS-SPNEGO and NTLM get disabled with the update, because they don't
  work properly with slapd in UCS (:uv:bug:`56868`).

* Due to frequent corruption of the on-disk SAML identity cache the default in
  multiprocessing mode has been changed to the in-memory cache. The |UCSUCRV|
  :envvar:`umc/saml/in-memory-identity-cache` has therefore been removed
  (:uv:bug:`54880`).

* The valid URI schemes for the SAML attribute consuming service and single
  logout endpoints are now configurable via the |UCSUCRV| :envvar:`umc/saml/schemes`
  (:uv:bug:`57060`).

* The |UCSUMC| has been prepared to support login via
  OpenID Connect, which is currently unsupported and therefore disabled by
  default (:uv:bug:`49006`).

* The HTML title and icon of |UCSUMC| is now configurable via the |UCSUCRV|\ s
  :envvar:`umc/web/title` and :envvar:`umc/web/favicon` (:uv:bug:`56917`).

* An icon that is shown in the UCS license import dialog in |UCSUMC| had to be
  replaced with a new one that has an OSI compliant license (:uv:bug:`56717`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* The replacement of the fallback |UCSUMC| logger has been adjusted to use
  :py:mod:`univention.logging` (:uv:bug:`55324`).

.. _changelog-umc-udmcli:

|UCSUDM| and command line interface
===================================

* The Univention Configuration Registry Policy |UCSUDM| module now has an attribute
  indicating that it supports being assigned to an object multiple times
  (:uv:bug:`57046`).

* A file descriptor leak in the |UCSUDM| CLI server has been fixed (:uv:bug:`57089`).

* Fix reaping terminated child processes (:uv:bug:`7735`).

* Fix a potential infinite loop in handling Samba logon hour syntax
  (:uv:bug:`28496`).

* Adjusted DNS object handling to fix compatibility with the UDM REST API
  (:uv:bug:`55555`).

* The cron job for deleting expired block list entries now runs only if block
  lists are activated (:uv:bug:`57102`).

* Fix escaping of DNS labels and names (:uv:bug:`50385`).

* Allow using domain ``home.arpa`` from :rfc:`8375` (:uv:bug:`55612`).

* The StartTLS operation mode is now configurable via the |UCSUCRV|
  :envvar:`directory/manager/starttls`. This is required in a Kubernetes environment
  (:uv:bug:`57098`).

* The log messages of |UCSUDM| are now logged via the Python :py:mod:`logging` interface,
  which is configured to still log to the :py:mod:`univention.debug` log stream. This
  is a prerequisite for prefixing log lines with the request ID in the UDM REST
  API (:uv:bug:`56970`).

* The :py:mod:`uldap` library now supports the SASL binding mechanism ``OAUTHBEARER``
  (:uv:bug:`49006`).

* On UCS 5.2 systems purely numeric user and group names are no longer allowed
  by default. The |UCSUCRV|\ s :envvar:`directory/manager/user/enable-legacy-username-format` and :envvar:`directory/manager/group/enable-legacy-cn-format` have been added
  to optionally allow such names if needed. System upgrades detect whether
  fully numeric names are already in use, in which case they are automatically
  allowed (:uv:bug:`56232`).

* The new logging interface :py:mod:`univention.logging` is used to initialize
  :py:mod:`univention.debug` (:uv:bug:`55324`).

* A missing dependency to :program:`python-univention-debug` has been added, which
  preserves Python 2.7 compatibility (:uv:bug:`57064`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* The |UCSUDM| CLI daemon is now restarted after setting the LDAP base during system
  setup (:uv:bug:`57039`).

* A incompatibility with newer versions of :program:`dnspython` has been fixed
  (:uv:bug:`56911`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* The diagnostic plugin for checking SAML (SSO) certificates now also supports
  the Keycloak identity provider (:uv:bug:`55976`).

* The diagnostic module :command:`31_file_permissions` has been extended to include
  sensitive files for OIDC configuration (:uv:bug:`49006`).

* A check has been added to verify that the LDAP server's configuration file
  has the file system permissions 0640 (:uv:bug:`57038`).

.. _changelog-umc-other:

Other modules
=============

* A |UCSUMC| module for blocklist lists and entries has been added (:uv:bug:`57043`).

* Existing Univention Configuration Registry policies attached to a container
  are no longer deleted when multiple ones previously existed and a new one is
  added (:uv:bug:`57046`).

* The error handling when super-ordinate objects don't exist has been repaired
  (:uv:bug:`55555`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* A new Python module :py:mod:`univention.logging` has been introduced which provides a
  Python :py:mod:`logging` handler for :py:mod:`univention.debug`. It allows software
  components to use the :py:mod:`logging` interface of Python while logging into a
  :py:mod:`univention.debug` stream (:uv:bug:`55324`).

* Log messages are no longer erroneously logged by the wrong logger when
  :py:mod:`univention.debug2` is used but :py:mod:`univention.logging` isn't imported
  (:uv:bug:`57026`).

* The detection of the correct log level has been repaired in case
  :py:mod:`univention.debug` was not initialized via :py:mod:`univention.logging`
  (:uv:bug:`57101`).

* The StartTLS operation mode is now configurable via the |UCSUCRV| :envvar:`directory/manager/starttls`. This is required in a Kubernetes environment
  (:uv:bug:`57098`).

* An unused dependency on :program:`py3dns` has been removed (:uv:bug:`56911`).

* The :py:mod:`uldap` library now supports the SASL binding mechanism ``OAUTHBEARER``
  (:uv:bug:`49006`).

* The log messages of :py:mod:`uldap` are now logged via the Python :py:mod:`logging`
  interface, which is configured to still log to the :py:mod:`univention.debug` log
  stream. This is a prerequisite for prefixing log lines with the request ID
  in the UDM REST API (:uv:bug:`56970`).

* The new LDAP database ``cn=internal`` has been added to store blocklist entries
  (:uv:bug:`57038`).

* The LDAP server has been extended with the ``OAUTHBEARER`` SASL mechanism,
  which is disabled by default (:uv:bug:`49006`).

* A memory leak in the UDM REST API has been fixed, which was caused by not
  discarding unused weak references in the :py:class:`univention.lib.i18n.Translation`
  (:uv:bug:`56420`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* On UCS 5.2 systems purely numeric user and group names are no longer allowed
  by default. The |UCSUCRV|\ s :envvar:`directory/manager/user/enable-legacy-username-format` and :envvar:`directory/manager/group/enable-legacy-cn-format` have been added
  to optionally allow such names if needed. System upgrades detect whether
  fully numeric names are already in use, in which case they are automatically
  allowed (:uv:bug:`56232`).

* :command:`univention-system-stats` collects system information periodically. One of
  the commands it uses is :command:`top`. The parameter ``c`` has been added to show the
  complete process command line in the output of :command:`top` (:uv:bug:`50567`).

.. _changelog-deployment-pkgdb:

Software monitor
================

* The dependency on :program:`py3dns` has been replaced by :program:`dnspython` to support EDNS,
  which is required for virtual machines on AWS-EC2 and OpenStack
  (:uv:bug:`56911`).

* The StartTLS operation mode is now configurable via the |UCSUCRV| :envvar:`directory/manager/starttls`. This is required in a Kubernetes environment
  (:uv:bug:`57098`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* The :command:`univention-keycloak` scripts has been extended to support more
  parameters for the :command:`init` command (:uv:bug:`57001`).

* The standard configuration for Keycloak has been changed to allow machine
  accounts to login (:uv:bug:`57100`).

* The package :program:`univention-keycloak` ships the command line script :command:`univention-
  keycloak-migration-status` which is used before the update to UCS 5.2 to
  check whether the migration to Keycloak is complete. The requirement to
  install the Keycloak app before the update has been dropped. The update to
  UCS 5.2 will be possible without the installation of the Keycloak app
  (:uv:bug:`56888`).

* Commands to manage proxy realms (supplemental logical IDP's in Keycloak that
  authenticate users on the default IDP) have been added to `univention-
  Keycloak` (:uv:bug:`56884`).

* The :command:`univention-keycloak` scripts has been extended to support more
  parameters for the ``oidc/rp`` creation (:uv:bug:`49006`).

.. _changelog-service-selfservice:

Univention self service
=======================

* The connection settings for the :program:`memcached` and :program:`PostgreSQL` databases are now
  configurable via |UCSUCRV|\ s. This is a requirement to run the self service
  in a containerized environment (:uv:bug:`57061`).

.. _changelog-service-mail:

Mail services
=============

* Avoid duplicate entries in :file:`/etc/fetchmailrc` when running a listener
  re-synchronization (:uv:bug:`56521`).

* Fixed migration script LDAP filter to only process user objects
  (:uv:bug:`57090`).

* The Fetchmail listener now writes atomically to :file:`/etc/fetchmailrc`
  (:uv:bug:`56587`).

.. _changelog-service-dovecot:

Dovecot
=======

* The type of the |UCSUCRV| :envvar:`mail/dovecot/logging/auth_verbose_passwords`
  has been changed to :py:obj:`str`, so that the validation in UCR strict type setting
  mode passes (:uv:bug:`56520`).

.. _changelog-service-radius:

RADIUS
======

* The |UCSUCRV| :envvar:`freeradius/conf/allow-mac-address-authentication` has been
  added to to allow authentication via MAC address and VLAN-assignment for
  computer objects. By default, this feature is disabled (:uv:bug:`56060`).

.. _changelog-service-other:

Other services
==============

* The directory :file:`/var/log/univention/listener_modules/` and
  :file:`/var/log/apt/history.log` are now also fetched in a Univention Support
  Information archive (:uv:bug:`56962`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* When joining a system to a UCS domain with a large number of objects in the
  LDAP directory, the script :command:`create_spn_account.sh` restarted the S4-Connector
  too often while waiting for the service principal name to appear in the
  Samba/AD SAM directory, possibly causing additional delay. This has been
  fixed (:uv:bug:`57027`).

* When stopping the samba processes, a process could remain e.g. bound to port
  135, causing problems for samba restarts. The script stopping the processes
  has been made more robust (:uv:bug:`56914`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* During normal replication objects with ``objectClass=lock`` are not replicated.
  But during initial join they were. By adjusting the filter in the listener
  module this is now avoided, speeding up initial replication
  (:uv:bug:`56954`).

* Initial join could take a long time in cases where customers have a lot of
  DNS records in Samba/AD. The joinscript now prioritizes objects (DNS zones
  etc) that are essential for operation of Samba/AD. This improves usability
  during initial joins and rejoins (:uv:bug:`56956`).

* Group member DNs with containing special characters that require escaping can
  be notated in different ways. When comparing them, this has not been taken
  into consideration, leading to rejects and tracebacks in the log file. This
  has been fixed (:uv:bug:`57072`).

* The StartTLS operation mode is now configurable via the |UCSUCRV|
  :envvar:`directory/manager/starttls`. This is required in a Kubernetes environment
  (:uv:bug:`57098`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* During normal replication objects with ``objectClass=lock`` are not replicated.
  But during initial join they were. By adjusting the filter in the listener
  module this is now avoided, speeding up initial replication
  (:uv:bug:`56954`).

* Group member DNs with containing special characters that require escaping can
  be notated in different ways. When comparing them, this has not been taken
  into consideration, leading to rejects and tracebacks in the log file. This
  has been fixed (:uv:bug:`57072`).

* The StartTLS operation mode is now configurable via the |UCSUCRV|
  :envvar:`directory/manager/starttls`. This is required in a Kubernetes environment
  (:uv:bug:`57098`).

.. _changelog-other:

*************
Other changes
*************

* A PAM and a SASL module for ``OAUTHBEARER`` (:rfc:`7628`) has been introduced
  (:uv:bug:`49006`).


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

# TODO

.. _security:

* All security updates issued for UCS 5.0-7 are included:

  * :program:`bind9` (:uv:cve:`2023-50387`, :uv:cve:`2023-50868`)
    (:uv:bug:`57301`)

  * :program:`bluez` (:uv:cve:`2023-27349`) (:uv:bug:`57342`)

  * :program:`containerd` (:uv:cve:`2020-15257`, :uv:cve:`2021-21334`,
    :uv:cve:`2021-41103`, :uv:cve:`2022-23471`, :uv:cve:`2022-23648`,
    :uv:cve:`2023-25153`, :uv:cve:`2023-25173`) (:uv:bug:`56457`)

  * :program:`curl` (:uv:cve:`2023-27534`) (:uv:bug:`57160`)

  * :program:`docker.io` (:uv:cve:`2021-21284`, :uv:cve:`2021-21285`,
    :uv:cve:`2021-41089`, :uv:cve:`2021-41091`, :uv:cve:`2021-41092`)
    (:uv:bug:`56457`)

  * :program:`emacs` (:uv:cve:`2024-30203`, :uv:cve:`2024-30204`,
    :uv:cve:`2024-30205`) (:uv:bug:`57250`)

  * :program:`expat` (:uv:cve:`2023-52425`) (:uv:bug:`57215`)

  * :program:`firefox-esr` (:uv:cve:`2023-5388`, :uv:cve:`2024-0743`,
    :uv:cve:`2024-2607`, :uv:cve:`2024-2608`, :uv:cve:`2024-2609`,
    :uv:cve:`2024-2610`, :uv:cve:`2024-2611`, :uv:cve:`2024-2612`,
    :uv:cve:`2024-2614`, :uv:cve:`2024-2616`, :uv:cve:`2024-29944`,
    :uv:cve:`2024-3302`, :uv:cve:`2024-3852`, :uv:cve:`2024-3854`,
    :uv:cve:`2024-3857`, :uv:cve:`2024-3859`, :uv:cve:`2024-3861`,
    :uv:cve:`2024-3864`, :uv:cve:`2024-4367`, :uv:cve:`2024-4767`,
    :uv:cve:`2024-4768`, :uv:cve:`2024-4769`, :uv:cve:`2024-4770`,
    :uv:cve:`2024-4777`) (:uv:bug:`57198`, :uv:bug:`57232`,
    :uv:bug:`57303`)

  * :program:`glib2.0` (:uv:cve:`2024-34397`) (:uv:bug:`57300`)

  * :program:`glibc` (:uv:cve:`2024-2961`) (:uv:bug:`57249`)

  * :program:`golang-1.13` (:uv:cve:`2020-16845`, :uv:cve:`2022-1705`,
    :uv:cve:`2022-27664`, :uv:cve:`2022-28131`, :uv:cve:`2022-2879`,
    :uv:cve:`2022-2880`, :uv:cve:`2022-30629`, :uv:cve:`2022-30631`,
    :uv:cve:`2022-30632`, :uv:cve:`2022-30633`, :uv:cve:`2022-30635`,
    :uv:cve:`2022-32148`, :uv:cve:`2022-32189`, :uv:cve:`2022-41717`,
    :uv:cve:`2023-24534`, :uv:cve:`2023-24537`, :uv:cve:`2023-24538`)
    (:uv:bug:`56457`)

  * :program:`golang-1.18` (:uv:cve:`2020-16845`, :uv:cve:`2022-1705`,
    :uv:cve:`2022-1962`, :uv:cve:`2022-27664`, :uv:cve:`2022-28131`,
    :uv:cve:`2022-2879`, :uv:cve:`2022-2880`, :uv:cve:`2022-29526`,
    :uv:cve:`2022-30629`, :uv:cve:`2022-30630`, :uv:cve:`2022-30631`,
    :uv:cve:`2022-30632`, :uv:cve:`2022-30633`, :uv:cve:`2022-30635`,
    :uv:cve:`2022-32148`, :uv:cve:`2022-32189`, :uv:cve:`2022-41715`,
    :uv:cve:`2022-41717`, :uv:cve:`2023-24534`, :uv:cve:`2023-24537`,
    :uv:cve:`2023-24538`) (:uv:bug:`56457`)

  * :program:`imagemagick` (:uv:cve:`2022-48541`) (:uv:bug:`57176`)

  * :program:`intel-microcode` (:uv:cve:`2023-22655`,
    :uv:cve:`2023-28746`, :uv:cve:`2023-38575`, :uv:cve:`2023-39368`,
    :uv:cve:`2023-43490`) (:uv:bug:`57252`)

  * :program:`libgd2` (:uv:cve:`2018-14553`, :uv:cve:`2021-38115`,
    :uv:cve:`2021-40812`) (:uv:bug:`57216`)

  * :program:`libnet-cidr-lite-perl` (:uv:cve:`2021-47154`)
    (:uv:bug:`57179`)

  * :program:`libvirt` (:uv:cve:`2020-10703`, :uv:cve:`2020-12430`,
    :uv:cve:`2020-25637`, :uv:cve:`2021-3631`, :uv:cve:`2021-3667`,
    :uv:cve:`2021-3975`, :uv:cve:`2021-4147`, :uv:cve:`2022-0897`,
    :uv:cve:`2024-1441`, :uv:cve:`2024-2494`, :uv:cve:`2024-2496`)
    (:uv:bug:`57199`)

  * :program:`nghttp2` (:uv:cve:`2024-28182`) (:uv:bug:`57251`)

  * :program:`nss` (:uv:cve:`2023-5388`, :uv:cve:`2024-0743`)
    (:uv:bug:`57152`)

  * :program:`openjdk-11` (:uv:cve:`2024-21011`, :uv:cve:`2024-21012`,
    :uv:cve:`2024-21068`, :uv:cve:`2024-21085`, :uv:cve:`2024-21094`)
    (:uv:bug:`57234`)

  * :program:`php7.3` (:uv:cve:`2022-31629`, :uv:cve:`2023-3823`,
    :uv:cve:`2024-2756`, :uv:cve:`2024-3096`) (:uv:bug:`57270`)

  * :program:`pillow` (:uv:cve:`2021-23437`, :uv:cve:`2022-22817`,
    :uv:cve:`2023-44271`, :uv:cve:`2024-28219`) (:uv:bug:`57180`,
    :uv:bug:`57225`)

  * :program:`postgresql-11` (:uv:cve:`2024-0985`) (:uv:bug:`57175`)

  * :program:`python-idna` (:uv:cve:`2024-3651`) (:uv:bug:`57272`)

  * :program:`python2.7` (:uv:cve:`2024-0450`) (:uv:bug:`57178`)

  * :program:`python3.7` (:uv:cve:`2023-6597`, :uv:cve:`2024-0450`)
    (:uv:bug:`57177`)

  * :program:`qemu` (:uv:cve:`2023-2861`, :uv:cve:`2023-3354`,
    :uv:cve:`2023-5088`) (:uv:bug:`57149`)

  * :program:`runc` (:uv:cve:`2021-30465`, :uv:cve:`2023-25809`,
    :uv:cve:`2023-27561`, :uv:cve:`2023-28642`, :uv:cve:`2024-21626`)
    (:uv:bug:`56457`)

  * :program:`shim` (:uv:cve:`2024-2312`) (:uv:bug:`57271`)

  * :program:`tar` (:uv:cve:`2023-39804`) (:uv:bug:`57150`)

  * :program:`tiff` (:uv:cve:`2023-3576`, :uv:cve:`2023-52356`)
    (:uv:bug:`57151`)

  * :program:`util-linux` (:uv:cve:`2021-37600`, :uv:cve:`2024-28085`)
    (:uv:bug:`57214`)

  * :program:`xorg-server` (:uv:cve:`2024-31080`,
    :uv:cve:`2024-31081`, :uv:cve:`2024-31083`) (:uv:bug:`57224`)


.. _debian:

* The following updated packages from Debian 10.13 are included:

  :program:`cacti`
  :program:`composer`
  :program:`distro-info-data`
  :program:`fossil`
  :program:`freeipa`
  :program:`frr`
  :program:`gross`
  :program:`gst-plugins-base1.0`
  :program:`gtkwave`
  :program:`jetty9`
  :program:`knot-resolver`
  :program:`less`
  :program:`libcaca`
  :program:`libdatetime-timezone-perl`
  :program:`libkf5ksieve`
  :program:`libpgjava`
  :program:`mediawiki`
  :program:`nodejs`
  :program:`node-xml2js`
  :program:`org-mode`
  :program:`putty`
  :program:`python-pymysql`
  :program:`qtbase-opensource-src`
  :program:`ruby-rack`
  :program:`shim-helpers-amd64-signed`
  :program:`trafficserver`
  :program:`tzdata`
  :program:`unadf`
  :program:`zfs-linux`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

.. _changelog-domain:

***************
Domain services
***************

* Fix dependency of server role packages to explicitly depend on a fixed
  version of Univention Configuration Registry. This fixes a regression caused
  by erratum 988 (:uv:bug:`57132`).

.. _changelog-udm:

LDAP Directory Manager
======================

* UDM has been adjusted to support declaring properties as lazy loading. If a
  property is lazy loading, it will only be fetched if explicitly requested.
  The flag ``--properties`` has been added to UDM CLI to request specific
  properties (:uv:bug:`57110`).

* If the UCR variable ``directory/manager/mail-address/uniqueness`` is set to
  ``true`` the uniqueness check for email addresses takes both user properties,
  ``mailPrimaryAddress`` and ``mailAlternativeAddress``, into account. It is now
  possible to swap the values for these properties with one change to the user
  object (:uv:bug:`57171`).

* The udm module ``settings/extended_attributes`` has been updated to include the
  property ``preventUmcDefaultPopup`` which is evaluated in the ``UMC`` and will
  inhibit it from warning the user that the default value of a property will be
  set during modification (:uv:bug:`51187`).

* A regression impacting the modification of ``users/ldap`` objects within the
  UMC has been addressed, stemming from Errata 1018 (:uv:bug:`57228`).

* Compatibility with Python 2.7 has been restored, which was broken by erratum
  991 (:uv:bug:`57146`).

* Added ability to filter for various attributes using the UDM commandline
  interface and in ``UMC``. This includes ``sambaLogonHours`` and
  ``accountActivationDate`` for the ``users/user`` module, ``hwaddress`` for the
  ``dhcp/host`` module and ``ip`` for the ``dns/ptr_record`` module (:uv:bug:`54339`,
  :uv:bug:`54339`, :uv:bug:`53830`, :uv:bug:`54339`, :uv:bug:`53830`,
  :uv:bug:`53807`, :uv:bug:`54339`, :uv:bug:`53830`, :uv:bug:`53807`,
  :uv:bug:`55604`).

* An asynchronous UDM REST API client has been added (:uv:bug:`56735`).

* A list of properties that should be returned by the REST API can be
  specified. As a default, all regular properties are returned. Lazy loading
  properties are only returned if explicitly requested (:uv:bug:`57110`).

* The LDAP overlay ``slapd-sock`` has ben enhanced by adding ``extendedresults``
  as a possible value to the ``sockresps`` configuration option. With that
  configuration, the overlay outputs a change LDIF in the ``RESULT`` phase,
  including LDAPControl data for ``PostReadControl`` and ``PreReadControl``
  collected during CRUD operations. The output format is similar to the one
  used by the LDAP overlay ``auditlog`` with an additional ``control:`` field
  (:uv:bug:`57267`).

* There is a new UCR variable ``directory/manager/feature/prepostread``
  to configure ``univention.uldap`` to send LDAPControls ``PostReadControl`` and
  ``PreReadControl`` for CRUD operations (``add``, ``modify``, ``modrdn``, ``delete``).
  If this option is activated the LDAPControls will instruct OpenLDAP to return
  all regular and operational attributes the are readable by the ``binddn`` before
  and after the change (:uv:bug:`57267`).

* UCS now allows configuring the LDAP overlay slapd-sock for
  ``sockresps extendedresults`` via UCR variable ``ldap/overlay/sock``.
  Once activated, it outputs LDAP changes including LDIF for CRUD operations
  (not for search).
  Additionally the UCR variable ``ldap/overlay/sock/sockops`` allows
  activating ``sockops add delete modify modrdn``. Please note that activating
  that second UCR variable causes the slapd process to wait for confirmation
  for CRUD events (see ``man slapd-sock``), so this must not be activated unless
  there is a suitable process responding to the socket path
  ``/var/lib/univention-ldap/slapd-sock/sock``. The purpose of these changes
  is to feed into the provisioning queue of Nubus (:uv:bug:`57267`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* When a user selects a different language inside the UMC, it was not used
  inside the modules. As example, the Server is on German, but a user selects
  English as their preferred language, the modules were still in German. This
  is fixed now, and the same language is used everywhere (:uv:bug:`57192`).

.. _changelog-umc-portal:

Univention Portal
=================

* In the past the user was not able to unset their birthday inside the self
  service, because the input validation did not detect a valid date according
  to the ISO-8601 standard. This is now possible again (:uv:bug:`57023`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* UMC now also logs the reason for a failed LDAP connection for module
  processes (:uv:bug:`57311`).

* The UMC SAML client is now updated in Keycloak on changes, e.g. when changing
  ``umc/saml/assertion-lifetime`` (:uv:bug:`57143`).

* A memory leak in the UMC server has been fixed (:uv:bug:`57104`).

* A LDAP connection leak in the UMC server has been fixed (:uv:bug:`57113`).

* The permission and ownership of the UMC log file is now only modified if it
  is not stdout or stderr (:uv:bug:`57154`).

* If the primary UCS server is on UCS version 5.2-0 or higher, UMC will no
  longer create or configure a client for simpleSAMLphp (:uv:bug:`57163`).

* The option ``copytruncate`` has been added to the ``logrotate`` configuration of
  UMC to not delete log files but to truncate the original log file to zero
  size in place (:uv:bug:`56906`).

* A missing Univention Configuration Registry Variable has been added to the
  trigger for the Apache2 ``univention.conf`` (:uv:bug:`57229`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* The ``UMC`` IP change module has been adapted to check the zone of the Single-
  Sign On domain name case insensitively (:uv:bug:`57290`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Add a diagnostic module to monitor the state of app queues (:uv:bug:`57217`).

.. _changelog-umc-policy:

Policies
========

* The StartTLS operation mode configured via the UCR variable
  ``directory/manager/starttls`` will now be used by univention-policy
  (:uv:bug:`57158`).

* The LDAP port configured via the UCR variable ``ldap/server/port`` will now be
  used by univention-policy (:uv:bug:`57159`).

* The StartTLS operation mode configured via the UCR variable
  ``directory/manager/starttls`` and the LDAP port configured via the UCR
  variable ``ldap/server/port`` will now be used by univention-policy
  (:uv:bug:`57173`).

* The StartTLS and ldap/server/port UCR variables have caused a regression
  where certain password lengths could not parsed anymore during LDAP bind.
  This change has been reverted to investigate the problem. If you updated to
  erratum 997, please update this package immediately (:uv:bug:`57169`).

* A compiler flag has been added to the building process to detect certain
  memory errors during the execution of ``univention_policy_results``
  (:uv:bug:`57257`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* All lazy loading properties are fetched by the UMC UDM module
  (:uv:bug:`57110`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* LDAP schema attributes for the UCS authorization engine (guardian) roles have
  been added (:uv:bug:`57110`).

* Even though all OCs inherit from top and actually are found when searching
  for ``(objectClass=top)``, the (inherited) ``objectClass: top`` does not show up
  as an attribute in the output of ``ldapsearch`` (:uv:bug:`50268`).

* The udm module ``settings/extended_attributes`` has been updated to include the
  property ``preventUmcDefaultPopup`` which is evaluated in the ``UMC`` and will
  inhibit it from warning the user that the default value of a property will be
  set during modification (:uv:bug:`51187`).

* Errata update 991 improved the LDAP filters for DNS objets in UDM but we
  forgot to add an LDAP index for the sOARecord attribute there. This update
  fixes that and should improve the performance of the UMC modules ``computers``
  and ``school computers``, especially for teachers in UCS@school environments,
  which are subject to a larger number of LDAP ACLs (:uv:bug:`57193`).

* New helper function ``ucs_needsKeycloakSetup``, ``ucs_needsSimplesamlphpSetup``
  and ``ucs_primaryVersionGreaterEqual`` have been added to easier evaluate what
  kind of SAML setup is needed the domain (:uv:bug:`57163`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* The LDAP filter for user objects in the LDAP federation configuration has
  been changed to require the attribute ``uid`` (:uv:bug:`57205`).

.. _changelog-service-radius:

RADIUS
======

* The RADIUS server now supports different MAC address formats for the MAB (MAC
  Authentication Bypass) feature (:uv:bug:`57069`).

* The default enabled configuration under ``/etc/freeradius/3.0/sites-enabled/``
  was reset to the default one during installation. This breaks setups with
  custom configurations (:uv:bug:`55007`).

.. _changelog-other:

*************
Other changes
*************

* Newer version of package is required as build time dependency for ``runc``,
  ``containerd`` and ``docker.io`` (:uv:bug:`56457`).

* Fix Debian Bug ``#960887``: ``Use of uninitialized value $caller``
  (:uv:bug:`56457`).


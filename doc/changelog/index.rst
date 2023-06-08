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

.. _security:

* UCS 5.0-8 includes all issued security updates issued for UCS 5.0-7:

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

* UCS 5.0-8 includes the following updated packages from Debian 10.13:

  :program:`cacti`,
  :program:`composer`,
  :program:`distro-info-data`,
  :program:`fossil`,
  :program:`freeipa`,
  :program:`frr`,
  :program:`gross`,
  :program:`gst-plugins-base1.0`,
  :program:`gtkwave`,
  :program:`jetty9`,
  :program:`knot-resolver`,
  :program:`less`,
  :program:`libcaca`,
  :program:`libdatetime-timezone-perl`,
  :program:`libkf5ksieve`,
  :program:`libpgjava`,
  :program:`mediawiki`,
  :program:`nodejs`,
  :program:`node-xml2js`,
  :program:`org-mode`,
  :program:`putty`,
  :program:`python-pymysql`,
  :program:`qtbase-opensource-src`,
  :program:`ruby-rack`,
  :program:`shim-helpers-amd64-signed`,
  :program:`trafficserver`,
  :program:`tzdata`,
  :program:`unadf`,
  :program:`zfs-linux`

.. _maintained:

* UCS 5.0-8 includes the following packages in the maintained repository of UCS:

  :program:`crudeoauth`

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

* Adjusted |UCSUDM| to support declaring properties as lazy loading.
  If a property is lazy loading, UCS only fetches it, if explicitly requested.
  Added the flag ``--properties`` to |UCSUDM| CLI to request specific properties (:uv:bug:`57110`).

* If the |UCSUCRV| :envvar:`directory/manager/mail-address/uniqueness` has the value ``true``,
  the uniqueness check for email addresses takes both user properties,
  ``mailPrimaryAddress`` and ``mailAlternativeAddress``, into account.
  It's now possible to swap the values for these properties with one change to the user object (:uv:bug:`57171`).

* Updated the |UCSUDM| module ``settings/extended_attributes`` to include the property ``preventUmcDefaultPopup``
  which UCS evaluates in the |UCSUMC|.
  It inhibits UCS from warning the user that a modification sets the default value of a property (:uv:bug:`51187`).

* Addressed a regression impacting the modification of ``users/ldap`` objects within the |UCSUMC|,
  stemming from erratum 1018 (:uv:bug:`57228`).

* Restored compatibility with Python 2.7, which erratum 991 has broken (:uv:bug:`57146`).

* Added ability to filter for various attributes using the |UCSUDM| command line interface and in |UCSUMC|.
  This includes ``sambaLogonHours`` and ``accountActivationDate`` for the ``users/user`` module,
  ``hwaddress`` for the ``dhcp/host`` module
  and ``ip`` for the ``dns/ptr_record`` module
  (:uv:bug:`54339`, :uv:bug:`54339`, :uv:bug:`53830`, :uv:bug:`54339`, :uv:bug:`53830`,
  :uv:bug:`53807`, :uv:bug:`54339`, :uv:bug:`53830`, :uv:bug:`53807`,
  :uv:bug:`55604`).

* Added an asynchronous |UCSREST| client (:uv:bug:`56735`).

* Administrators can specify a list of properties that |UCSREST| should return.
  As a default behavior, |UCSREST| returns all regular properties.
  |UCSREST| only returns lazy loading properties, if explicitly requested (:uv:bug:`57110`).

* Enhanced the LDAP overlay ``slapd-sock`` by adding ``extendedresults`` as a possible value to the ``sockresps`` configuration option.
  With that configuration, the overlay outputs a changed LDIF in the ``RESULT`` phase,
  including *LDAPControl* data for ``PostReadControl`` and ``PreReadControl`` collected during CRUD operations.
  The output format is similar to the one used by the LDAP overlay ``auditlog`` with an additional ``control:`` field (:uv:bug:`57267`).

* Added the |UCSUCRV| :envvar:`directory/manager/feature/prepostread`
  to configure :py:mod:`univention.uldap`
  to send *LDAPControls* ``PostReadControl`` and ``PreReadControl``
  for the CRUD operations ``add``, ``modify``, ``modrdn``, and ``delete``.
  If UCS has this option activated,
  the *LDAPControls* instruct OpenLDAP to return all regular and operational attributes
  that are readable by the ``binddn`` before and after the change (:uv:bug:`57267`).

* UCS now allows configuring the LDAP overlay ``slapd-sock`` for ``sockresps extendedresults`` through the |UCSUCRV| :envvar:`ldap/overlay/sock`.
  If activated, it outputs LDAP changes including LDIF for CRUD operations, not for search.
  Additionally, the |UCSUCRV| :envvar:`ldap/overlay/sock/sockops` allows activating ``sockops add delete modify modrdn``.

  Please note that activating that second |UCSUCRV|
  causes the :program:`slapd` process to wait for confirmation for CRUD events, see :command:`man slapd-sock`.
  So, you mustn't activate it,
  unless there is a suitable process responding to the socket path :file:`/var/lib/univention-ldap/slapd-sock/sock`.
  The purpose of these changes is to feed into the provisioning queue of Nubus (:uv:bug:`57267`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* When a user selects a different language inside the |UCSUMC|,
  it didn't use the language inside the modules.
  For example, the server provides German,
  but a user selects English as their preferred language,
  the modules were still in German. Fixed it and |UCSUMC| uses the same language everywhere (:uv:bug:`57192`).

.. _changelog-umc-portal:

Univention Portal
=================

* In the past the user wasn't able to unset their birthday inside the self service,
  because the input validation didn't detect a valid date according to the ISO-8601 standard.
  Users can unset their birthday again (:uv:bug:`57023`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* |UCSUMC| now also logs the reason for a failed LDAP connection for module processes (:uv:bug:`57311`).

* The |UCSUMC| |SAML| client is now updated in Keycloak on changes,
  for example when changing the |UCSUCRV| :envvar:`umc/saml/assertion-lifetime` (:uv:bug:`57143`).

* Fixed a memory leak in the |UCSUMC| server (:uv:bug:`57104`).

* Fixed a LDAP connection leak in the |UCSUMC| server (:uv:bug:`57113`).

* The permission and ownership of the |UCSUMC| log file is now only modified if it
  isn't ``STDOUT`` or ``STDERR`` (:uv:bug:`57154`).

* If the UCS primary directory node is on UCS version 5.2-0 or higher,
  |UCSUMC| no longer creates or configures a client for ``simpleSAMLphp`` (:uv:bug:`57163`).

* Added the option ``copytruncate`` to the :program:`logrotate` configuration of |UCSUMC|
  to not delete log files,
  but to truncate the original log file to zero size in place (:uv:bug:`56906`).

* Added a missing |UCSUCRV| to the trigger the :program:`apache2` :file:`univention.conf` (:uv:bug:`57229`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* Adapted the |UCSUMC| IP change module to check the zone of the single sign-n domain name case insensitively (:uv:bug:`57290`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Added a diagnostic module to monitor the state of app queues (:uv:bug:`57217`).

.. _changelog-umc-policy:

Policies
========

* ``univention-policy`` uses the ``StartTLS`` operation mode configured through the |UCSUCRV|
  :envvar:`directory/manager/starttls` (:uv:bug:`57158`, :uv:bug:`57173`).

* ``univention-policy`` uses the LDAP port configured through the |UCSUCRV|
  :envvar:`ldap/server/port` (:uv:bug:`57159`, :uv:bug:`57173`).

* Added a compiler flag to the building process
  to detect certain memory errors during the execution of :command:`univention_policy_result` (:uv:bug:`57257`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* The |UCSUMC| |UCSUDM| module fetches all lazy loading properties (:uv:bug:`57110`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* Added the LDAP schema attributes for the UCS authorization engine *Guardian* roles (:uv:bug:`57110`).

* Even though all OCs inherit from top and :command:`ldapsearch` actually finds them when searching
  for ``(objectClass=top)``,
  the (inherited) ``objectClass: top`` doesn't show up as an attribute in the output of :command:`ldapsearch` (:uv:bug:`50268`).

* Updated the |UCSUDM| module ``settings/extended_attributes`` to include the property ``preventUmcDefaultPopup``
  which UCS evaluates in the |UCSUMC|.
  It inhibits UCS from warning the user that a modification sets the default value of a property (:uv:bug:`51187`).

* Erratum 991 improved the LDAP filters for DNS objects in |UCSUDM|,
  but forgot to add an LDAP index for the ``sOARecord`` attribute there.
  This update fixes that and improves the performance of the |UCSUMC| modules ``computers`` and ``school computers``,
  especially for teachers in UCS\@school environments,
  which are subject to a larger number of LDAP ACLs (:uv:bug:`57193`).

* Added the helper functions ``ucs_needsKeycloakSetup``, ``ucs_needsSimplesamlphpSetup``, and ``ucs_primaryVersionGreaterEqual``
  to easier evaluate what kind of |SAML| setup the domain needs (:uv:bug:`57163`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* Changed the LDAP filter for user objects in the LDAP federation configuration
  to require the attribute ``uid`` (:uv:bug:`57205`).

.. _changelog-service-radius:

RADIUS
======

* The RADIUS server now supports different MAC address formats for the MAB (MAC
  Authentication Bypass) feature (:uv:bug:`57069`).

* The default enabled configuration under :file:`/etc/freeradius/3.0/sites-enabled/`
  was reset to the default one during installation. This breaks setups with
  custom configurations (:uv:bug:`55007`).

.. _changelog-service-cups:

Printing services
=================

* :program:`CUPS` now uses the UCS TLS certificate instead of a self-signed
  certificate (:uv:bug:`52879`).

.. _changelog-other:

*************
Other changes
*************

* Newer version of package is required as build time dependency for :program:`runc`,
  :program:`containerd` and :program:`docker.io` (:uv:bug:`56457`).

* Fix Debian Bug ``#960887``: ``Use of uninitialized value $caller``
  (:uv:bug:`56457`).

* Updated the following product logos: login page icon, ``favicon``, portal icon, and |UCSUMC| portal entry icon (:uv:bug:`57378`).

* Added the GPG/PGP public key :file:`univention-archive-key-ucs-52x.gpg` for UCS version 5.2.
  This key signs the UCS version 5.2 repository (:uv:bug:`57312`).

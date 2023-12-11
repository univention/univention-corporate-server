.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
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

* All security updates issued for UCS 5.0-5 are included:

  * :program:`c-ares` (:uv:cve:`2020-22217`) (:uv:bug:`56608`)

  * :program:`cups` (:uv:cve:`2023-32360`, :uv:cve:`2023-4504`)
    (:uv:bug:`56679`)

  * :program:`curl` (:uv:cve:`2023-28321`, :uv:cve:`2023-38546`)
    (:uv:bug:`56745`)

  * :program:`dbus` (:uv:cve:`2023-34969`) (:uv:bug:`56778`)

  * :program:`elfutils` (:uv:cve:`2020-21047`) (:uv:bug:`56652`)

  * :program:`exim4` (:uv:cve:`2023-42114`, :uv:cve:`2023-42116`)
    (:uv:bug:`56706`)

  * :program:`firefox-esr` (:uv:cve:`2022-23597`, :uv:cve:`2022-2505`,
    :uv:cve:`2022-36315`, :uv:cve:`2022-36316`, :uv:cve:`2022-36318`,
    :uv:cve:`2022-36319`, :uv:cve:`2022-36320`, :uv:cve:`2022-38472`,
    :uv:cve:`2022-38473`, :uv:cve:`2022-38475`, :uv:cve:`2022-38477`,
    :uv:cve:`2022-38478`, :uv:cve:`2022-40674`, :uv:cve:`2022-40956`,
    :uv:cve:`2022-40957`, :uv:cve:`2022-40958`, :uv:cve:`2022-40959`,
    :uv:cve:`2022-40960`, :uv:cve:`2022-40962`, :uv:cve:`2022-42927`,
    :uv:cve:`2022-42928`, :uv:cve:`2022-42929`, :uv:cve:`2022-42930`,
    :uv:cve:`2022-42931`, :uv:cve:`2022-42932`, :uv:cve:`2022-45403`,
    :uv:cve:`2022-45404`, :uv:cve:`2022-45405`, :uv:cve:`2022-45406`,
    :uv:cve:`2022-45407`, :uv:cve:`2022-45408`, :uv:cve:`2022-45409`,
    :uv:cve:`2022-45410`, :uv:cve:`2022-45411`, :uv:cve:`2022-45412`,
    :uv:cve:`2022-45415`, :uv:cve:`2022-45416`, :uv:cve:`2022-45417`,
    :uv:cve:`2022-45418`, :uv:cve:`2022-45419`, :uv:cve:`2022-45420`,
    :uv:cve:`2022-45421`, :uv:cve:`2022-46871`, :uv:cve:`2022-46872`,
    :uv:cve:`2022-46873`, :uv:cve:`2022-46874`, :uv:cve:`2022-46877`,
    :uv:cve:`2022-46878`, :uv:cve:`2022-46879`, :uv:cve:`2023-0767`,
    :uv:cve:`2023-23598`, :uv:cve:`2023-23601`, :uv:cve:`2023-23602`,
    :uv:cve:`2023-23603`, :uv:cve:`2023-23604`, :uv:cve:`2023-23605`,
    :uv:cve:`2023-23606`, :uv:cve:`2023-25728`, :uv:cve:`2023-25729`,
    :uv:cve:`2023-25730`, :uv:cve:`2023-25731`, :uv:cve:`2023-25732`,
    :uv:cve:`2023-25733`, :uv:cve:`2023-25735`, :uv:cve:`2023-25736`,
    :uv:cve:`2023-25737`, :uv:cve:`2023-25739`, :uv:cve:`2023-25741`,
    :uv:cve:`2023-25742`, :uv:cve:`2023-25744`, :uv:cve:`2023-25745`,
    :uv:cve:`2023-25750`, :uv:cve:`2023-25751`, :uv:cve:`2023-25752`,
    :uv:cve:`2023-28160`, :uv:cve:`2023-28161`, :uv:cve:`2023-28162`,
    :uv:cve:`2023-28164`, :uv:cve:`2023-28176`, :uv:cve:`2023-28177`,
    :uv:cve:`2023-29533`, :uv:cve:`2023-29535`, :uv:cve:`2023-29536`,
    :uv:cve:`2023-29537`, :uv:cve:`2023-29538`, :uv:cve:`2023-29539`,
    :uv:cve:`2023-29540`, :uv:cve:`2023-29541`, :uv:cve:`2023-29543`,
    :uv:cve:`2023-29544`, :uv:cve:`2023-29547`, :uv:cve:`2023-29548`,
    :uv:cve:`2023-29549`, :uv:cve:`2023-29550`, :uv:cve:`2023-29551`,
    :uv:cve:`2023-32205`, :uv:cve:`2023-32206`, :uv:cve:`2023-32207`,
    :uv:cve:`2023-32208`, :uv:cve:`2023-32209`, :uv:cve:`2023-32210`,
    :uv:cve:`2023-32211`, :uv:cve:`2023-32212`, :uv:cve:`2023-32213`,
    :uv:cve:`2023-32215`, :uv:cve:`2023-32216`, :uv:cve:`2023-34414`,
    :uv:cve:`2023-34415`, :uv:cve:`2023-34416`, :uv:cve:`2023-34417`,
    :uv:cve:`2023-3482`, :uv:cve:`2023-3600`, :uv:cve:`2023-37201`,
    :uv:cve:`2023-37202`, :uv:cve:`2023-37203`, :uv:cve:`2023-37204`,
    :uv:cve:`2023-37205`, :uv:cve:`2023-37206`, :uv:cve:`2023-37207`,
    :uv:cve:`2023-37208`, :uv:cve:`2023-37209`, :uv:cve:`2023-37210`,
    :uv:cve:`2023-37211`, :uv:cve:`2023-37212`, :uv:cve:`2023-4045`,
    :uv:cve:`2023-4046`, :uv:cve:`2023-4047`, :uv:cve:`2023-4048`,
    :uv:cve:`2023-4049`, :uv:cve:`2023-4050`, :uv:cve:`2023-4051`,
    :uv:cve:`2023-4053`, :uv:cve:`2023-4055`, :uv:cve:`2023-4056`,
    :uv:cve:`2023-4057`, :uv:cve:`2023-4573`, :uv:cve:`2023-4574`,
    :uv:cve:`2023-4575`, :uv:cve:`2023-4577`, :uv:cve:`2023-4578`,
    :uv:cve:`2023-4580`, :uv:cve:`2023-4581`, :uv:cve:`2023-4583`,
    :uv:cve:`2023-4584`, :uv:cve:`2023-4585`, :uv:cve:`2023-4863`,
    :uv:cve:`2023-5169`, :uv:cve:`2023-5171`, :uv:cve:`2023-5176`,
    :uv:cve:`2023-5217`, :uv:cve:`2023-5721`, :uv:cve:`2023-5724`,
    :uv:cve:`2023-5725`, :uv:cve:`2023-5728`, :uv:cve:`2023-5730`,
    :uv:cve:`2023-5732`, :uv:cve:`2023-6204`, :uv:cve:`2023-6205`,
    :uv:cve:`2023-6206`, :uv:cve:`2023-6207`, :uv:cve:`2023-6208`,
    :uv:cve:`2023-6209`, :uv:cve:`2023-6212`) (:uv:bug:`56607`,
    :uv:bug:`56676`, :uv:bug:`56780`, :uv:bug:`56876`)

  * :program:`firmware-nonfree` (:uv:cve:`2022-27635`,
    :uv:cve:`2022-36351`, :uv:cve:`2022-38076`, :uv:cve:`2022-40964`,
    :uv:cve:`2022-46329`) (:uv:bug:`56683`)

  * :program:`flac` (:uv:cve:`2020-22219`) (:uv:bug:`56653`)

  * :program:`ghostscript` (:uv:cve:`2020-21710`,
    :uv:cve:`2020-21890`) (:uv:bug:`56655`)

  * :program:`glib2.0` (:uv:cve:`2023-29499`, :uv:cve:`2023-32611`,
    :uv:cve:`2023-32665`) (:uv:bug:`56654`)

  * :program:`gnutls28` (:uv:cve:`2023-5981`) (:uv:bug:`56877`)

  * :program:`grub-efi-amd64-signed` (:uv:cve:`2023-4692`,
    :uv:cve:`2023-4693`) (:uv:bug:`56742`)

  * :program:`grub2` (:uv:cve:`2023-4692`, :uv:cve:`2023-4693`)
    (:uv:bug:`56742`)

  * :program:`krb5` (:uv:cve:`2023-36054`) (:uv:bug:`56755`)

  * :program:`libde265` (:uv:cve:`2023-27102`, :uv:cve:`2023-27103`,
    :uv:cve:`2023-43887`, :uv:cve:`2023-47471`) (:uv:bug:`56892`)

  * :program:`libwebp` (:uv:cve:`2023-4863`) (:uv:bug:`56633`)

  * :program:`libx11` (:uv:cve:`2023-43785`, :uv:cve:`2023-43786`,
    :uv:cve:`2023-43787`) (:uv:bug:`56741`)

  * :program:`libxpm` (:uv:cve:`2023-43788`, :uv:cve:`2023-43789`)
    (:uv:bug:`56744`)

  * :program:`memcached` (:uv:cve:`2022-48571`) (:uv:bug:`56738`)

  * :program:`ncurses` (:uv:cve:`2020-19189`, :uv:cve:`2021-39537`,
    :uv:cve:`2023-29491`) (:uv:bug:`56684`, :uv:bug:`56893`)

  * :program:`nghttp2` (:uv:cve:`2020-11080`, :uv:cve:`2023-44487`)
    (:uv:bug:`56740`)

  * :program:`nss` (:uv:cve:`2020-25648`, :uv:cve:`2023-4421`)
    (:uv:bug:`56779`)

  * :program:`openjdk-11` (:uv:cve:`2023-21930`, :uv:cve:`2023-21937`,
    :uv:cve:`2023-21938`, :uv:cve:`2023-21939`, :uv:cve:`2023-21954`,
    :uv:cve:`2023-21967`, :uv:cve:`2023-21968`, :uv:cve:`2023-22006`,
    :uv:cve:`2023-22036`, :uv:cve:`2023-22041`, :uv:cve:`2023-22045`,
    :uv:cve:`2023-22049`, :uv:cve:`2023-22081`, :uv:cve:`2023-25193`)
    (:uv:bug:`56632`, :uv:bug:`56776`)

  * :program:`poppler` (:uv:cve:`2020-23804`, :uv:cve:`2022-37050`,
    :uv:cve:`2022-37051`) (:uv:bug:`56746`)

  * :program:`postgresql-11` (:uv:cve:`2023-2454`,
    :uv:cve:`2023-2455`, :uv:cve:`2023-5868`, :uv:cve:`2023-5869`,
    :uv:cve:`2023-5870`) (:uv:bug:`56677`, :uv:bug:`56821`)

  * :program:`python-reportlab` (:uv:cve:`2019-19450`,
    :uv:cve:`2020-28463`) (:uv:bug:`56678`)

  * :program:`python-urllib3` (:uv:cve:`2018-20060`,
    :uv:cve:`2018-25091`, :uv:cve:`2019-11236`, :uv:cve:`2019-11324`,
    :uv:cve:`2020-26137`, :uv:cve:`2023-43803`, :uv:cve:`2023-43804`)
    (:uv:bug:`56743`, :uv:bug:`56822`)

  * :program:`python2.7` (:uv:cve:`2021-23336`, :uv:cve:`2022-0391`,
    :uv:cve:`2022-48560`, :uv:cve:`2022-48565`, :uv:cve:`2022-48566`,
    :uv:cve:`2023-24329`, :uv:cve:`2023-40217`) (:uv:bug:`56644`)

  * :program:`python3.7` (:uv:cve:`2022-48560`, :uv:cve:`2022-48564`,
    :uv:cve:`2022-48565`, :uv:cve:`2022-48566`, :uv:cve:`2023-40217`)
    (:uv:bug:`56739`)

  * :program:`samba` (:uv:cve:`2023-3961`, :uv:cve:`2023-4091`,
    :uv:cve:`2023-4154`, :uv:cve:`2023-42669`, :uv:cve:`2023-42670`)
    (:uv:bug:`56696`)

  * :program:`univention-directory-listener` (:uv:cve:`2023-38994`)
    (:uv:bug:`56354`)

  * :program:`univention-directory-manager-modules`
    (:uv:cve:`2023-38994`) (:uv:bug:`56354`)

  * :program:`univention-directory-replication` (:uv:cve:`2023-38994`)
    (:uv:bug:`56354`)

  * :program:`univention-ldap` (:uv:cve:`2023-38994`)
    (:uv:bug:`56333`, :uv:bug:`56767`)

  * :program:`univention-licence` (:uv:cve:`2023-38994`)
    (:uv:bug:`56354`)

  * :program:`univention-nagios` (:uv:cve:`2023-38994`)
    (:uv:bug:`56354`)

  * :program:`univention-samba` (:uv:cve:`2023-38994`)
    (:uv:bug:`56332`)

  * :program:`univention-samba4` (:uv:cve:`2023-38994`)
    (:uv:bug:`56354`)

  * :program:`vim` (:uv:cve:`2023-4752`, :uv:cve:`2023-4781`)
    (:uv:bug:`56675`)

  * :program:`xorg-server` (:uv:cve:`2023-5367`, :uv:cve:`2023-5380`)
    (:uv:bug:`56777`)


.. _debian:

* The following updated packages from Debian 10.13 are included:

  :program:`activemq`
  :program:`amanda`
  :program:`asmtools`
  :program:`audiofile`
  :program:`axis`
  :program:`batik`
  :program:`cargo-mozilla`
  :program:`ceph`
  :program:`cryptojs`
  :program:`distro-info`
  :program:`distro-info-data`
  :program:`e2guardian`
  :program:`exempi`
  :program:`freeimage`
  :program:`freerdp2`
  :program:`frr`
  :program:`gerbv`
  :program:`gimp`
  :program:`gimp-dds`
  :program:`gnome-boxes`
  :program:`gsl`
  :program:`h2o`
  :program:`horizon`
  :program:`inetutils`
  :program:`jetty9`
  :program:`jtreg6`
  :program:`libapache-mod-jk`
  :program:`libclamunrar`
  :program:`libcue`
  :program:`libvpx`
  :program:`libyang`
  :program:`lldpd`
  :program:`lwip`
  :program:`minizip`
  :program:`mutt`
  :program:`netty`
  :program:`node-babel`
  :program:`node-browserify-sign`
  :program:`node-cookiejar`
  :program:`node-json5`
  :program:`opendkim`
  :program:`org-mode`
  :program:`orthanc`
  :program:`phppgadmin`
  :program:`pmix`
  :program:`postgresql-multicorn`
  :program:`prometheus-alertmanager`
  :program:`python-requestbuilder`
  :program:`qemu`
  :program:`redis`
  :program:`reportbug`
  :program:`request-tracker4`
  :program:`roundcube`
  :program:`ruby-loofah`
  :program:`ruby-rails-html-sanitizer`
  :program:`ruby-rmagick`
  :program:`ruby-sanitize`
  :program:`rust-cbindgen`
  :program:`rustc-mozilla`
  :program:`strongswan`
  :program:`tang`
  :program:`testng7`
  :program:`thunderbird`
  :program:`tomcat9`
  :program:`trapperkeeper-webserver-jetty9-clojure`
  :program:`vinagre`
  :program:`vlc`
  :program:`zbar`
  :program:`zookeeper`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

  :program:`py-lmdb` (:uv:bug:`53387`)

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* The configuration file :file:`/etc/selinux/config` has been added to disable SELinux.
  SELinux is not supported by UCS (:uv:bug:`56005`).

.. _changelog-domain-openldap:

OpenLDAP
========

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* Some new attributes that will be provided by OpenLDAPs :program:`ppolicy` from version
  2.5 on, were removed from the schema replication exclusion list, to allow
  interoperability with the new OpenLDAP version (:uv:bug:`56729`).

* The script :command:`univention-directory-replication` created a temporary password
  file with a newline in it, which therefore contained an invalid password.
  This resulted in :program:`slapd` not being able to import a file :file:`failed.ldif` on
  startup. This fixes a regression from :uv:erratum:`5.0x870` (:uv:bug:`56801`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* The request header ``If-Match`` can now be given in ``DELETE`` requests to make
  them conditional (:uv:bug:`56731`).

* Missing properties when creating or modifying objects are now correctly
  marked in the error response (:uv:bug:`56734`).

* The unsupported HTML developer view of the UDM REST API has been disabled and
  can be enabled via the |UCSUCRV| :envvar:`directory/manager/rest/html-view-
  enabled` (:uv:bug:`56714`).

* Duplicate settings for the Keycloak app have been removed from the theme
  styles (:uv:bug:`56548`).

* The error handling for progress bars has been improved so that Apache
  restarts during app installations don't cause failures anymore
  (:uv:bug:`56562`).

.. _changelog-umc-portal:

Univention Portal
=================

* The deletion of a user's profile picture via :program:`Self Service` has been repaired
  (:uv:bug:`56349`).

* The labels of the :program:`Self Service` forms were always displayed in English when
  they were accessed directly via URL without navigating through the portal.
  They are now translated correctly (:uv:bug:`56660`).

* Update file :file:`portals.json` atomically to prevent inconsistent reading
  (:uv:bug:`53860`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* The detection of active requests has been corrected so that module processes
  cannot be exited anymore if there are still open requests. This was broken
  since :uv:bug:`56198` :uv:erratum:`5.0x721` (:uv:bug:`56575`).

* The configured maximum request body size is now respected (:uv:bug:`56510`).

* The maximum number of parallel HTTP connections from the UMC-Server to UMC
  module processes has been raised from 10 to unlimited (:uv:bug:`56828`).

* User preferences (such as favorite |UCSUMC| modules) could not be set via old UMC
  clients from UCS systems before UCS 5.0-3. The functionality has been restored
  (:uv:bug:`56753`).

* Explicit defaults for cookie settings were added to
  :file:`/var/www/univention/meta.json` so they are available for all components that
  needs them (:uv:bug:`56703`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* A broken internal JSON file will no longer crash the :program:`univention-appcenter-listener-converter`. If a broken JSON file is found, it will be skipped and
  logged in the log file :file:`/var/log/univention/listener_modules/<app id>.log`
  (:uv:bug:`56421`).

.. _changelog-umc-udmcli:

|UCSUDM| and command line interface
===================================

* The ``If-Match`` request header can now be given in ``DELETE`` requests to the
  UDM REST API to make them conditional (:uv:bug:`56731`).

* Missing properties when creating or modifying objects via the UDM REST API
  are now correctly marked in the error response (:uv:bug:`56734`).

* The unused UDM properties from Nagios server have been marked as optional to
  ease the upgrade to UCS 5.2 (:uv:bug:`56820`).

* The Python 3.11 compatibility for timezone handling has been repaired
  (:uv:bug:`56514`).

* The case sensitivity of the attribute ``memberUid`` is now respected when
  removing members from a group (:uv:bug:`54183`).

* The command :program:`univention-admin` has been removed.
  It was deprecated since UCS 3.0 (:uv:bug:`53802`).

.. _changelog-umc-join:

Domain join module
==================

* The join-scripts are now executed with ``umask 022`` instead of the restrictive
  ``umask 077`` from the UMC Server (:uv:bug:`53431`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Include new diagnostic module to check if PostgreSQL is migrated to version
  11 (:uv:bug:`56773`).

* The text :guilabel:`Success` is no longer displayed when a check failed after all
  checks have previously passed (:uv:bug:`56624`).

* Include new diagnostic module to check the correct setting of |UCSUCRV| :envvar:`ldap/master` (:uv:bug:`48548`).

.. _changelog-umc-quota:

File system quota module
========================

* Querying users for a partition runs into a timeout after 10 minutes when
  there are many users (:uv:bug:`56575`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* The registration of LDAP schema files failed if the schema file is the first
  file in the directory and there is already a local schema file with the same
  name which was not registered via LDAP (:uv:bug:`56857`).

* The unused LDAP attributes from Nagios server have been marked as optional to
  ease the upgrade to UCS 5.2 (:uv:bug:`56820`).

* :uv:erratum:`5.0x785` introduced a new mechanism in :command:`ucs_registerLDAPExtension` to re-
  trigger the activation of an LDAP ACL or schema extension by doing a trivial
  (i.e. no-op) LDAP modification. This failed on the Primary node due to
  missing credentials. :command:`ucs_registerLDAPExtension` has been fixed to use the
  LDAP admin connection in this case (:uv:bug:`56698`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* The software update module will not show :guilabel:`UCS 5.1-0` as available version for
  upgrade because it is an intermediate version between UCS 5.0 and UCS 5.2 to
  which an upgrade will not be possible (:uv:bug:`56517`).

* The internal tool :program:`ucslint` is now independent from the current working directory.
  It has been fully converted to Python 3.7 code, which changes the API for its plugins.
  Performance has also been improved and several small bugs have been fixed.
  This found several new issues in other packages, which previously had not been detected.
  Some of them have also been fixed (:uv:bug:`55668`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* :command:`univention-keycloak init` is now able to be executed again in case of a
  failure during first initialization. The option ``--force`` has been added to
  force the rerun of the initialization (:uv:bug:`56791`).

* A script which checks the migration status from SimpleSAMLPHP / OpenID
  Connector Provider to Keycloak has been added to the package :program:`univention-keycloak`
  (:uv:bug:`56747`).

* The commands :command:`messages` and :command:`login-links` have been added to manage Keycloak
  message bundles and login links for the login page (:uv:bug:`56478`).

* The Python 2.7 compatibility for the |UCSUCR| template file
  :file:`/etc/simplesamlphp/00authsources.php` has been restored (:uv:bug:`56588`) and was ported back to UCS 5.0-4 (:uv:bug:`56647`).

* A workaround has been added which prevents a potential LDAP schema
  registration failure (:uv:bug:`56857`).

* :uv:erratum:`5.0x881` broke mixed environments with UCS 4.4. Therefore the UDM modules
  are now only registered for UCS 5 based systems (:uv:bug:`56864`).

* The LDAP schema and UDM modules are now registered in the LDAP and therefore
  replicated to all servers in the domain to ease the upgrade to UCS 5.2
  (:uv:bug:`56824`).

.. _changelog-service-mail:

Mail services
=============

* The detection whether a user is a :program:`Fetchmail` user (by checking if they have an attribute
  ``mailPrimaryAddress``) during modifications of users has been repaired.
  Therefore when the ``mailPrimaryAddress`` is changed or removed the correct
  changes are synchronized to :program:`Fetchmail` (:uv:bug:`56482`).

* Deleting :program:`Fetchmail` configurations of a user now correctly removes entries
  from the file :file:`fetchmailrc` in case they are the last ones (:uv:bug:`56426`).

* Narrowed down the conditions under which the |UCSUDL| module gets called
  (:uv:bug:`56586`).

.. _changelog-service-dhcp:

DHCP server
===========

* The network installer has been converted from a SysV init script into a :program:`systemd` unit.
  URLs configured for |UCSUCRV| :envvar:`repository/online/server` are now handled correctly.

.. _changelog-service-pam:

PAM / Local group cache
=======================

* Future compatibility with :program:`sudo` version 1.9.4 has been added, where additional
  environment variables need to be passed explicitly to sub-processes
  (:uv:bug:`56579`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* :command:`univention-samba4-backup` now uses the :command:`samba-tool` backup command to create
  a backup of the Samba database and the directory :file:`syslog` (:uv:bug:`56434`).

* The |UCSUCRV|\ s :envvar:`samba/database/backend/store` and
  :envvar:`samba/database/backend/store/size` have been added to configure the Samba
  database backend (``tdb`` or ``mdb``) before the initial setup, join or re-join
  (:uv:bug:`56401`).

* The Samba package now recommends the package :program:`python3-lmdb` (:uv:bug:`53387`).

* Under certain conditions, installation of the package :program:`univention-samba4` aborted because of a missing package dependency on a specific version of :program:`samba-dsdb-modules`, when an older version of that package was already installed.
  This is addressed by making the package :program:`univention-samba4` depend on the meta-package :program:`samba-ad-dc` instead, and letting that manage a versioned dependency on :program:`samba-dsdb-modules`.
  This simplifies the package dependencies (:uv:bug:`56794`).

* The package :program:`samba-ad-dc` now depends on a specific version of :program:`samba-dsdb-modules` to upgrade the initially installed version to the one required during installation.
  This addresses issues when an ISO was used for installation that did not already include the latest Samba provided by errata updates (:uv:bug:`56794`).

* The package :program:`samba-ad-dc` now depends on a specific version of :program:`samba-ad-provision`, instead of only recommending it.
  This addresses issues when installing directly from the UCS 5.0-6 ISO image (:uv:bug:`56870`).

* The modified dependency of :program:`univention-samba4` on :program:`samba-ad-dc` introduced by :uv:erratum:`5.0x890` caused :program:`libnss-winbind` to be installed.
  This package modified file:`/etc/nsswitch.conf` adding ``winbind`` to it. This has been reverted (:uv:bug:`56885`).

* Symbolic links in the directory :file:`sysvol` will no longer break the Samba backup tool (:uv:bug:`56866`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* Starting with UCS 5.0 the |UCSS4c| converted POSIX-only groups to Samba
  groups. This was a regression compared to the behavior in UCS 4.4. Now the
  mapping offers a new key ``auto_enable_udm_option`` that is disabled by default
  and is only activated for the UDM property ``userCertificate``, allowing
  changes of UDM object options just in that special case (:uv:bug:`56772`).

* Future compatibility for :program:`python3-ldap` >= 4 has been added (:uv:bug:`56603`).

* Future compatibility for :program:`python3-samba` has been added (:uv:bug:`56537`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* During synchronization from an MS AD forest child domain, the |UCSADC| may
  receive DNs that refer to objects outside the scope of the child domain. In
  that case it receives an LDAP referral which caused a python traceback. The
  |UCSADC| now skips referrals to objects and logs an informative message
  instead (:uv:bug:`56792`).

* The |UCSADC| failed to handle forest child domains (:uv:bug:`53944`).

* Future compatibility for :program:`python3-ldap` >= 4 has been added (:uv:bug:`56603`).


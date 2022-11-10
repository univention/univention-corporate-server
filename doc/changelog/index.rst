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

* All security updates issued for UCS 5.0-3 are included:

  * :program:`xorg-server` (:uv:cve:`2023-0494`, :uv:cve:`2023-1393`)
    (:uv:bug:`55675`, :uv:bug:`55934`)

  * :program:`unbound` (:uv:cve:`2020-28935`, :uv:cve:`2022-30698`,
    :uv:cve:`2022-30699`, :uv:cve:`2022-3204`) (:uv:bug:`55932`)

  * :program:`tiff` (:uv:cve:`2023-0795`, :uv:cve:`2023-0796`,
    :uv:cve:`2023-0797`, :uv:cve:`2023-0798`, :uv:cve:`2023-0799`,
    :uv:cve:`2023-0800`, :uv:cve:`2023-0801`, :uv:cve:`2023-0802`,
    :uv:cve:`2023-0803`, :uv:cve:`2023-0804`) (:uv:bug:`55736`)

  * :program:`systemd` (:uv:cve:`2023-26604`) (:uv:bug:`55928`)

  * :program:`samba` (:uv:cve:`2023-0614`, :uv:cve:`2023-0922`)
    (:uv:bug:`55892`)

  * :program:`qemu` () (:uv:bug:`55881`)

  * :program:`python2.7` (:uv:cve:`2015-20107`, :uv:cve:`2019-20907`,
    :uv:cve:`2020-26116`, :uv:cve:`2020-8492`, :uv:cve:`2021-3177`,
    :uv:cve:`2021-3733`, :uv:cve:`2021-3737`, :uv:cve:`2021-4189`,
    :uv:cve:`2022-45061`) (:uv:bug:`56101`)

  * :program:`python-ipaddress` (:uv:cve:`2020-14422`)
    (:uv:bug:`56079`)

  * :program:`python-cryptography` (:uv:cve:`2023-23931`)
    (:uv:bug:`55739`)

  * :program:`postgresql-11` (:uv:cve:`2022-41862`,
    :uv:cve:`2023-2454`, :uv:cve:`2023-2455`) (:uv:bug:`55676`,
    :uv:bug:`56061`)

  * :program:`php7.3` (:uv:cve:`2022-31631`, :uv:cve:`2023-0567`,
    :uv:cve:`2023-0568`, :uv:cve:`2023-0662`) (:uv:bug:`55759`)

  * :program:`pcre2` (:uv:cve:`2019-20454`, :uv:cve:`2022-1586`,
    :uv:cve:`2022-1587`) (:uv:bug:`55897`)

  * :program:`openssl` (:uv:cve:`2022-2097`, :uv:cve:`2022-4304`,
    :uv:cve:`2022-4450`, :uv:cve:`2023-0215`, :uv:cve:`2023-0286`)
    (:uv:bug:`55737`)

  * :program:`nss` (:uv:cve:`2020-12400`, :uv:cve:`2020-12401`,
    :uv:cve:`2020-12403`, :uv:cve:`2020-6829`, :uv:cve:`2023-0767`)
    (:uv:bug:`55735`)

  * :program:`mariadb-10.3` (:uv:cve:`2022-47015`) (:uv:bug:`56117`)

  * :program:`linux-signed-amd64` (:uv:cve:`2022-2873`,
    :uv:cve:`2022-3424`, :uv:cve:`2022-3545`, :uv:cve:`2022-36280`,
    :uv:cve:`2022-3707`, :uv:cve:`2022-41218`, :uv:cve:`2022-45934`,
    :uv:cve:`2022-4744`, :uv:cve:`2022-47929`, :uv:cve:`2023-0045`,
    :uv:cve:`2023-0266`, :uv:cve:`2023-0394`, :uv:cve:`2023-0458`,
    :uv:cve:`2023-0459`, :uv:cve:`2023-0461`, :uv:cve:`2023-1073`,
    :uv:cve:`2023-1074`, :uv:cve:`2023-1078`, :uv:cve:`2023-1079`,
    :uv:cve:`2023-1118`, :uv:cve:`2023-1281`, :uv:cve:`2023-1513`,
    :uv:cve:`2023-1670`, :uv:cve:`2023-1829`, :uv:cve:`2023-1855`,
    :uv:cve:`2023-1859`, :uv:cve:`2023-1989`, :uv:cve:`2023-1990`,
    :uv:cve:`2023-1998`, :uv:cve:`2023-2162`, :uv:cve:`2023-2194`,
    :uv:cve:`2023-23454`, :uv:cve:`2023-23455`, :uv:cve:`2023-23559`,
    :uv:cve:`2023-26545`, :uv:cve:`2023-28328`, :uv:cve:`2023-30456`,
    :uv:cve:`2023-30772`) (:uv:bug:`56032`)

  * :program:`linux-latest` (:uv:cve:`2022-2873`, :uv:cve:`2022-3424`,
    :uv:cve:`2022-3545`, :uv:cve:`2022-36280`, :uv:cve:`2022-3707`,
    :uv:cve:`2022-41218`, :uv:cve:`2022-45934`, :uv:cve:`2022-4744`,
    :uv:cve:`2022-47929`, :uv:cve:`2023-0045`, :uv:cve:`2023-0266`,
    :uv:cve:`2023-0394`, :uv:cve:`2023-0458`, :uv:cve:`2023-0459`,
    :uv:cve:`2023-0461`, :uv:cve:`2023-1073`, :uv:cve:`2023-1074`,
    :uv:cve:`2023-1078`, :uv:cve:`2023-1079`, :uv:cve:`2023-1118`,
    :uv:cve:`2023-1281`, :uv:cve:`2023-1513`, :uv:cve:`2023-1670`,
    :uv:cve:`2023-1829`, :uv:cve:`2023-1855`, :uv:cve:`2023-1859`,
    :uv:cve:`2023-1989`, :uv:cve:`2023-1990`, :uv:cve:`2023-1998`,
    :uv:cve:`2023-2162`, :uv:cve:`2023-2194`, :uv:cve:`2023-23454`,
    :uv:cve:`2023-23455`, :uv:cve:`2023-23559`, :uv:cve:`2023-26545`,
    :uv:cve:`2023-28328`, :uv:cve:`2023-30456`, :uv:cve:`2023-30772`)
    (:uv:bug:`56032`)

  * :program:`linux` (:uv:cve:`2022-2873`, :uv:cve:`2022-3424`,
    :uv:cve:`2022-3545`, :uv:cve:`2022-36280`, :uv:cve:`2022-3707`,
    :uv:cve:`2022-41218`, :uv:cve:`2022-45934`, :uv:cve:`2022-4744`,
    :uv:cve:`2022-47929`, :uv:cve:`2023-0045`, :uv:cve:`2023-0266`,
    :uv:cve:`2023-0394`, :uv:cve:`2023-0458`, :uv:cve:`2023-0459`,
    :uv:cve:`2023-0461`, :uv:cve:`2023-1073`, :uv:cve:`2023-1074`,
    :uv:cve:`2023-1078`, :uv:cve:`2023-1079`, :uv:cve:`2023-1118`,
    :uv:cve:`2023-1281`, :uv:cve:`2023-1513`, :uv:cve:`2023-1670`,
    :uv:cve:`2023-1829`, :uv:cve:`2023-1855`, :uv:cve:`2023-1859`,
    :uv:cve:`2023-1989`, :uv:cve:`2023-1990`, :uv:cve:`2023-1998`,
    :uv:cve:`2023-2162`, :uv:cve:`2023-2194`, :uv:cve:`2023-23454`,
    :uv:cve:`2023-23455`, :uv:cve:`2023-23559`, :uv:cve:`2023-26545`,
    :uv:cve:`2023-28328`, :uv:cve:`2023-30456`, :uv:cve:`2023-30772`)
    (:uv:bug:`56032`)

  * :program:`libxml2` (:uv:cve:`2023-28484`, :uv:cve:`2023-29469`)
    (:uv:bug:`56033`)

  * :program:`libwebp` (:uv:cve:`2023-1999`) (:uv:bug:`56118`)

  * :program:`libde265` (:uv:cve:`2023-24751`, :uv:cve:`2023-24752`,
    :uv:cve:`2023-24754`, :uv:cve:`2023-24755`, :uv:cve:`2023-24756`,
    :uv:cve:`2023-24757`, :uv:cve:`2023-24758`, :uv:cve:`2023-25221`)
    (:uv:bug:`55780`)

  * :program:`ldb` (:uv:cve:`2023-0614`) (:uv:bug:`55892`)

  * :program:`intel-microcode` (:uv:cve:`2022-21216`,
    :uv:cve:`2022-21233`, :uv:cve:`2022-33196`, :uv:cve:`2022-33972`,
    :uv:cve:`2022-38090`) (:uv:bug:`55933`)

  * :program:`imagemagick` (:uv:cve:`2020-19667`,
    :uv:cve:`2020-25665`, :uv:cve:`2020-25666`, :uv:cve:`2020-25674`,
    :uv:cve:`2020-25675`, :uv:cve:`2020-25676`, :uv:cve:`2020-27560`,
    :uv:cve:`2020-27750`, :uv:cve:`2020-27751`, :uv:cve:`2020-27754`,
    :uv:cve:`2020-27756`, :uv:cve:`2020-27757`, :uv:cve:`2020-27758`,
    :uv:cve:`2020-27759`, :uv:cve:`2020-27760`, :uv:cve:`2020-27761`,
    :uv:cve:`2020-27762`, :uv:cve:`2020-27763`, :uv:cve:`2020-27764`,
    :uv:cve:`2020-27765`, :uv:cve:`2020-27766`, :uv:cve:`2020-27767`,
    :uv:cve:`2020-27768`, :uv:cve:`2020-27769`, :uv:cve:`2020-27770`,
    :uv:cve:`2020-27771`, :uv:cve:`2020-27772`, :uv:cve:`2020-27773`,
    :uv:cve:`2020-27774`, :uv:cve:`2020-27775`, :uv:cve:`2020-27776`,
    :uv:cve:`2020-29599`, :uv:cve:`2021-20176`, :uv:cve:`2021-20224`,
    :uv:cve:`2021-20241`, :uv:cve:`2021-20243`, :uv:cve:`2021-20244`,
    :uv:cve:`2021-20245`, :uv:cve:`2021-20246`, :uv:cve:`2021-20309`,
    :uv:cve:`2021-20312`, :uv:cve:`2021-20313`, :uv:cve:`2021-3574`,
    :uv:cve:`2021-3596`, :uv:cve:`2021-39212`, :uv:cve:`2022-28463`,
    :uv:cve:`2022-32545`, :uv:cve:`2022-32546`, :uv:cve:`2022-32547`,
    :uv:cve:`2022-44267`, :uv:cve:`2022-44268`) (:uv:bug:`55869`,
    :uv:bug:`55896`, :uv:bug:`56081`)

  * :program:`heimdal` (:uv:cve:`2022-3437`, :uv:cve:`2022-45142`)
    (:uv:bug:`55674`)

  * :program:`gnutls28` (:uv:cve:`2023-0361`) (:uv:bug:`55723`)

  * :program:`ghostscript` () (:uv:bug:`55948`)

  * :program:`freeradius` (:uv:cve:`2022-41859`, :uv:cve:`2022-41860`,
    :uv:cve:`2022-41861`) (:uv:bug:`55758`)

  * :program:`firmware-nonfree` (:uv:cve:`2020-12362`,
    :uv:cve:`2020-12363`, :uv:cve:`2020-12364`, :uv:cve:`2020-24586`,
    :uv:cve:`2020-24587`, :uv:cve:`2020-24588`, :uv:cve:`2021-23168`,
    :uv:cve:`2021-23223`, :uv:cve:`2021-37409`, :uv:cve:`2021-44545`,
    :uv:cve:`2022-21181`) (:uv:bug:`55935`)

  * :program:`firefox-esr` (:uv:cve:`2023-0767`, :uv:cve:`2023-1945`,
    :uv:cve:`2023-25728`, :uv:cve:`2023-25729`, :uv:cve:`2023-25730`,
    :uv:cve:`2023-25732`, :uv:cve:`2023-25735`, :uv:cve:`2023-25737`,
    :uv:cve:`2023-25739`, :uv:cve:`2023-25742`, :uv:cve:`2023-25744`,
    :uv:cve:`2023-25746`, :uv:cve:`2023-25751`, :uv:cve:`2023-25752`,
    :uv:cve:`2023-28162`, :uv:cve:`2023-28164`, :uv:cve:`2023-28176`,
    :uv:cve:`2023-29533`, :uv:cve:`2023-29535`, :uv:cve:`2023-29536`,
    :uv:cve:`2023-29539`, :uv:cve:`2023-29541`, :uv:cve:`2023-29548`,
    :uv:cve:`2023-29550`, :uv:cve:`2023-32205`, :uv:cve:`2023-32206`,
    :uv:cve:`2023-32207`, :uv:cve:`2023-32211`, :uv:cve:`2023-32212`,
    :uv:cve:`2023-32213`, :uv:cve:`2023-32215`) (:uv:bug:`55720`,
    :uv:bug:`55895`, :uv:bug:`55974`, :uv:bug:`56062`)

  * :program:`emacs` (:uv:cve:`2022-48337`, :uv:cve:`2022-48339`,
    :uv:cve:`2023-28617`) (:uv:bug:`56063`)

  * :program:`curl` (:uv:cve:`2023-23916`, :uv:cve:`2023-27533`,
    :uv:cve:`2023-27535`, :uv:cve:`2023-27536`, :uv:cve:`2023-27538`)
    (:uv:bug:`55760`, :uv:bug:`56011`)

  * :program:`cups-filters` () (:uv:bug:`55886`, :uv:bug:`56082`)

  * :program:`cups` (:uv:cve:`2023-32324`) (:uv:bug:`56116`)

  * :program:`cpio` (:uv:cve:`2019-14866`, :uv:cve:`2021-38185`)
    (:uv:bug:`56115`)

  * :program:`clamav` (:uv:cve:`2023-20032`, :uv:cve:`2023-20052`)
    (:uv:bug:`55734`)

  * :program:`avahi` (:uv:cve:`2023-1981`) (:uv:bug:`56034`)

  * :program:`apr-util` (:uv:cve:`2022-25147`) (:uv:bug:`55738`)

  * :program:`apache2` (:uv:cve:`2006-20001`, :uv:cve:`2021-33193`,
    :uv:cve:`2022-36760`, :uv:cve:`2022-37436`, :uv:cve:`2023-25690`,
    :uv:cve:`2023-27522`) (:uv:bug:`55778`, :uv:bug:`56013`)



.. _debian:

* The following updated packages from Debian 10.13 are included:
  :program:`389-ds-base`,
  :program:`amanda`,
  :program:`asterisk`,
  :program:`binwalk`,
  :program:`c-ares`,
  :program:`connman`,
  :program:`distro-info-data`,
  :program:`duktape`,
  :program:`epiphany-browser`,
  :program:`git`,
  :program:`gitlab-workhorse`,
  :program:`golang-1.11`,
  :program:`golang-github-opencontainers-selinux`,
  :program:`golang-websocket`,
  :program:`graphite-web`,
  :program:`grunt`,
  :program:`haproxy`,
  :program:`hugo`,
  :program:`jackson-databind`,
  :program:`joblib`,
  :program:`jruby`,
  :program:`json-smart`,
  :program:`kamailio`,
  :program:`keepalived`,
  :program:`kopanocore`,
  :program:`libapache2-mod-auth-mellon`,
  :program:`libapache2-mod-auth-openidc`,
  :program:`libdatetime-timezone-perl`,
  :program:`libgit2`,
  :program:`libmicrohttpd`,
  :program:`libraw`,
  :program:`libreoffice`,
  :program:`libsdl2`,
  :program:`libssh`,
  :program:`linux-5.10`,
  :program:`linux-signed-5.10-amd64`,
  :program:`lldpd`,
  :program:`mono`,
  :program:`mpv`,
  :program:`nbconvert`,
  :program:`netatalk`,
  :program:`node-css-what`,
  :program:`nodejs`,
  :program:`node-nth-check`,
  :program:`node-url-parse`,
  :program:`nvidia-graphics-drivers-legacy-390xx`,
  :program:`openimageio`,
  :program:`openjdk-11`,
  :program:`openvswitch`,
  :program:`protobuf`,
  :program:`python-django`,
  :program:`python-werkzeug`,
  :program:`rainloop`,
  :program:`redis`,
  :program:`ruby2.5`,
  :program:`ruby-rack`,
  :program:`ruby-sidekiq`,
  :program:`shim-signed`,
  :program:`sniproxy`,
  :program:`snort`,
  :program:`sofia-sip`,
  :program:`sox`,
  :program:`spip`,
  :program:`sqlite`,
  :program:`sqlparse`,
  :program:`sssd`,
  :program:`svgpp`,
  :program:`syslog-ng`,
  :program:`sysstat`,
  :program:`texlive-bin`,
  :program:`thunderbird`,
  :program:`tomcat9`,
  :program:`trafficserver`,
  :program:`tzdata`,
  :program:`udisks2`,
  :program:`webkit2gtk`,
  :program:`wireless-regdb`,
  :program:`wireshark`,
  :program:`xapian-core`,
  :program:`xfig`,
  :program:`xrdp`,
  :program:`zabbix`

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* A wrong Python format string in the :program:`rsyslog` configuration has been fixed,
  which is used by |UCSUCRV| :envvar:`syslog/input/{udp,tcp,relp}` (:uv:bug:`56042`).

* Allow NFS shares to be mounted on exporting host itself to prevent data-loss
  on shared access (:uv:bug:`50193`).

* The deprecated command :command:`univention-keyboardmapping` has been removed
  (:uv:bug:`50193`).

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* The fix for :uv:bug:`54986` introduced an issue with the handling of `start-
  stop-daemon` that could result in an error message during :command:`systemctl restart
  univention-directory-notifier` (:uv:bug:`55957`).

* Implement :command:`univention-translog reinex` to re-built the transaction index file
  in case it gets corrupted. Univention Directory Notifier already has code to
  do maintain the index, but after certain error cases the index may become
  corrupt and has to be re-built. The code in UDN is not optimized to re-index
  many transactions in batch and shows performance issues for large transaction
  files (:uv:bug:`54797`).

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* It is now possible to access UDM modules with numbers in its name via the UDM
  REST API (:uv:bug:`55551`).

* The debug level is now correctly passed to child processes if it is set via
  UCR (:uv:bug:`56051`).

* Updated the copyright file. We do not ship icons from ``iconmonstr.com`` since
  UCS 5.0 (:uv:bug:`55862`).

* Form input fields that load values now show a standby animation
  (:uv:bug:`56053`).

.. _changelog-umc-portal:

Univention Portal
=================

* The Portal is now able to display announcements, which are realized via a
  new UDM module **portals/announcement** (:uv:bug:`55175`).

* The old UDM modules for the UCS 4.4 Portal have been renamed to better distinguish between
  them in the web user interface (:uv:bug:`55409`).

* The documentation wasn't specific enough about what command to run, after the
  |UCSUCRV| :envvar:`portal/default-dn` changed. Running :command:`univention-portal update`
  after changing the |UCSUCRV| is enough (:uv:bug:`55871`).

* The :guilabel:`Choose a tab` dialog box will now display tabs with their background
  color (:uv:bug:`55919`).

* Updating the portal information now uses a local UDM connection, thus
  removing potential load on the Primary Node in big environments
  (:uv:bug:`56113`).

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* The self-service notifications no longer show mixed language (English and
  German) when users modify their profile or change their password
  (:uv:bug:`55664`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* Disable the SOAP binding for single sign-out in the identity provider
  metadata to make sure we don't use SOAP for the UMC SAML logout
  (:uv:bug:`56069`).

* The joinscript now uses Python 3 instead of Python 2 to update SAML metadata.
  Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* The error message shown during password reset or change now appends the text
  from the |UCSUCRV| :envvar:`umc/login/password-complexity-message/.*` when
  password complexity criteria are not matched (:uv:bug:`55529`).

* The usage of multiple languages in various messages, such as notifications,
  has been eliminated (:uv:bug:`55664`).

* For UCS 5.0-3 the UMC services where converted to :program:`systemd`. These services are
  essential to continue running even when updates are installed from UMC. Due
  to an oversight the first :uv:erratum:`5.0x583` triggered a latent bug, which causes
  the service to stop during the upgrade, which kills any web session and abort
  the update process running in the background. This update adds a mitigation
  to prevent the service from stopping during the update (:uv:bug:`55753`).

* A missing Python 2.7 dependency has been added so that UMC modules using
  Python 2.7 work again (:uv:bug:`55752`).

* Building the downstream package *Univention System Setup* failed because of
  some missing package dependencies in *Univention Management Console*. They
  had been added with UCS 5.0-3 and changed by :uv:erratum:`5.0x595`, but were added to
  the wrong binary packages (:uv:bug:`55776`).

* A crash of the UMC-Server and UMC-Web-Server is now prevented
  (:uv:bug:`55959`).

* The |UCSUCR| template for the Apache configuration in UMC multiprocessing mode has
  been repaired (:uv:bug:`55726`).

* The UMC joinscript won't overwrite the |UCSUCRV| :envvar:`umc/saml/idp-server`
  during execution (:uv:bug:`55951`).

* The script :command:`univention-management-console-client` now accesses UMC via the
  HTTP interface instead of the deprecated UMCP (:uv:bug:`55913`).

* Some missing German translations have been added (:uv:bug:`56010`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* The message and the button label in the UMC App Center presented when a
  pinned App should be removed or upgraded was made more consistent
  (:uv:bug:`55679`).

* Some installation code is now executed with Python 3 instead of Python 2.
  Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* The App Center listener now removes files from its queue that contain
  ``entryUUIDs`` whose corresponding UDM objects cannot be found. These files
  cannot be processed by the listener and would otherwise remain in the queue
  forever and cause infinite error logging (:uv:bug:`56072`).

* The command :command:`univention-app shell` now supports the option ``--service_name``
  to specify the docker compose service name where the command is executed in
  (:uv:bug:`56038`).

* Error messages during app installations are now being translated
  (:uv:bug:`55664`).

* The App Center now supports adding custom settings to an app with a file
  :file:`/var/lib/univention-appcenter/apps/$APP_ID/custom.settings`. This file has
  the same format as the standard App Center settings file (:uv:bug:`55765`).

.. _changelog-umc-udmcli:

|UCSUDM| and command line interface
===================================

* The usability of the shares module has been overworked (:uv:bug:`44997`, :uv:bug:`40599`, :uv:bug:`7843`, :uv:bug:`31388`, :uv:bug:`42805`, :uv:bug:`44997`, :uv:bug:`50701`, :uv:bug:`53785`, :uv:bug:`19868`, :uv:bug:`21349`).

* The Simple UDM API now has a parameter to initialize a machine connection
  against the local :program:`slapd` (:uv:bug:`56113`).

* Newly set passwords are now always added to the password history even if the
  check for password history is disabled (:uv:bug:`56020`).

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* The syntax for ``IComputer_FQDN`` was using a wrong regular expression, which
  did accept some invalid values and was also susceptible to a regular
  expression denial of service vulnerability (:uv:bug:`33684`).

* Problems during concurrently reloading of UDM modules have been resolved
  (:uv:bug:`54597`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

.. _changelog-umc-join:

Domain join module
==================

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* The binary package :program:`univention-management-console-module-join` has been split
  from the source package :program:`univention-join` into a separate one to prevent a
  circular build dependency (:uv:bug:`55870`).

* The package is now using the latest :program:`ldb` version (:uv:bug:`55892`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Two messages in the SAML certificate diagnostic check contained a
  typographical error (typo) in the German translation. The messages show up
  when the diagnostic check complains about SAML certificates. The typo has
  been fixed (:uv:bug:`55874`).

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

.. _changelog-umc-quota:

File system quota module
========================

* Translations for the search bar in the UMC module :guilabel:`Filesystem quotas` have been
  added (:uv:bug:`55664`).

.. _changelog-umc-other:

Other modules
=============

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* A regression in :uv:erratum:`5.0x683` during package installation in |UCSUSS| has
  been corrected (:uv:bug:`56111`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* Fix the link to the release notes of future UCS releases (:uv:bug:`55667`).

* Fixed a regression where the UCS updater did ignore the URL path of
  components when creating the list of repositories in the file
  :file:`/etc/apt/sources.list.d/20_ucs-online-component.list` (:uv:bug:`55636`).

* A pre update check is now executed with Python 3 instead of Python 2
  (:uv:bug:`55632`).

.. _changelog-service-docker:

Docker
======

* Containers using glibc version 2.34 or above require the system calls
  ``clone3`` and ``faccessat2``. These system calls have been added to the default
  docker :program:`seccomp` rules that are used by single container apps in the App Center.
  (:uv:bug:`55360`).

.. _changelog-service-saml:

SAML
====

* :program:`SimpleSAMLPHP` is configured as a service provider in Keycloak, meaning it
  acts as a proxy and uses Keycloak as a backend. This is part of the
  migration from :program:`SimpleSAMLPHP` to Keycloak in UCS (:uv:bug:`56074`).

* New commands have been added to :program:`univention-keycloak` to create attribute
  mappers from the LDAP object to the internal Keycloak object (``user-
  attribute-ldap-mapper``) and to create *user attribute* mappers and *name identifiers*
  mappers for SAML clients (``saml-client-user-attribute-mapper``, ``saml-client-
  nameid-mapper``, :uv:bug:`56096`).

* The package :program:`univention-keycloak` now supports the ``keycloak/server/sso/path``
  app setting from the Keycloak app (:uv:bug:`56022`).

* The command :command:`upgrade-config` has been added to :program:`univention-keycloak`. This is
  used during upgrades of the Keycloak app to update the domain wide Keycloak
  configuration (:uv:bug:`55866`).

* Sub-commands for registering LDAP mapper, password update and self service
  extensions have been added to :program:`univention-keycloak` (:uv:bug:`55663`).

.. _changelog-service-selfservice:

Univention self service
=======================

* A regression introduced in UCS 5.0-3 has been fixed, which caused that
  accessing available password reset methods was not possible anymore
  (:uv:bug:`55684`).

* The error message shown during password reset or when creating a new account
  now appends the text from the |UCSUCRV| :envvar:`umc/login/password-complexity-
  message/.*` when password complexity criteria are not matched (:uv:bug:`55529`).

* Self-service
  user attributes specified in |UCSUCRV| :envvar:`self-service/udm_attributes` can be configured
  as read-only via the |UCSUCRV| :envvar:`self-service/udm_attributes/read-only` (:uv:bug:`55733`).

.. _changelog-service-mail:

Mail services
=============

* The migration of Fetchmail extended attributes has been moved to the
  joinscript :file:`univenition-fetchmail` to fix errors in environments where
  :program:`univention-fetchmail` is installed on a non-primary node. The old extended
  attributes have also been restored to fix errors in environments where
  :program:`univention-fetchmail` is running on a server that has not yet been upgraded
  (:uv:bug:`55882`).

* New checks have been added to the script :command:`migrate-fetchmail.py` to avoid errors
  during execution when a Fetchmail configuration is incomplete
  (:uv:bug:`55893`).

* Fixed error in UDM caused by the syntax of Fetchmail extended attributes. The
  bug occurred when hooks of other extended attributes of the user module
  initialize a UDM module (e.g ``settings/extended_attribuets``, :uv:bug:`55910`).

* Fix error in joinscript :file:`univention-fetchmail-schema` execution caused by a
  script. On member nodes now the correct credentials are used to connect to
  LDAP. Also it is checked if file :file:`/etc/fetchmailrc` exists (:uv:bug:`55766`).

* The hooks, syntax files and scripts are now installed on the package
  :program:`univention-fetchmail-schema` to avoid errors in installations where
  :program:`univention-fetchmail` is installed on Managed Nodes or Replica Directory
  Nodes (:uv:bug:`55681`).

* The listener module :file:`fetchmail` now correctly loads the file
  :file:`/etc/fetchmailrc` when there are entries from UIDs with a single character
  or with other valid characters like "'" (:uv:bug:`55682`).

.. _changelog-service-print:

Printing services
=================

* Updates no longer overwrite existing print-server configuration values with
  the defaults (:uv:bug:`55860`).

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

* :program:`cups` has been updated, so that printing multiple copies now works
  (:uv:bug:`55886`).

.. _changelog-service-radius:

RADIUS
======

* It is now possible to login with the mail primary address in addition to the
  username (:uv:bug:`55757`).

* The maximum TLS version has been changed to 1.2 in order to prevent issues
  with Windows 10 and 11 clients. The maximum TLS version can be specified via
  the |UCSUCRV| :envvar:`freeradius/conf/tls-max-version` (:uv:bug:`55247`).

.. _changelog-service-proxy:

Proxy services
==============

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

.. _changelog-win-samba:

Samba
=====

* The AD password change has been moved to another package to avoid problems on
  system that doesn't have :program:`univention-samba` installed (:uv:bug:`54390`).

* The logrotate configuration for :program:`samba-dcerpcd` and :program:`:program:samba-bgqd` has been
  fixed (:uv:bug:`55597`).

* The final restart of Samba at the end of a package update has been adjusted
  to the new daemon signature in the process list (:uv:bug:`55677`).

* Under special conditions, the Listener module :file:`samba4-idmap.py` wrote invalid
  values in the attributes ``xidNumber`` of the file :file:`idmap.ldb`. During package
  update they will be fixed (:uv:bug:`55686`).

* When uploading printer drivers, PE files with a higher version now replace
  older files, regardless of the case of the filename (:uv:bug:`52051`).

* The Samba init scripts :file:`samba-ad-dc` and :file:`samba` now also stop the services
  :program:`samba-dcerpcd` and :program:`samba-bgqd` (:uv:bug:`55727`).

* In scenarios where a UCS AD domain is run next to a native Microsoft AD
  domain with an AD-Connector mirroring users and password hashes between both
  the option ``auth methods`` is usually adjusted on the UCS AD DCs to make
  access to SMB shares hosted on UCS member servers possible for Microsoft AD
  users without needing to type in their password again. Since UCS 5.0 this
  broke Samba logon on the UCS AD DCs themselves. The Samba patch has been
  adjusted to only consider the method ``sam_ignoredomain`` from the list of
  values specified via the |UCSUCRV| :envvar:`samba/global/options/"auth methods"`
  or directly in the Samba :file:`local.conf` as configuration parameter ``auth
  methods``. If Samba finds this particular method in the Samba configuration,
  then it now only appends it to the standard list of authentication methods,
  rather than replacing the standard list completely. This approach should be
  more robust with respect to Samba release updates (:uv:bug:`55727`).

* Running the init script :file:`samba-ad-dc` with the operation ``restart`` left Samba
  in a state that didn't recognize non-local domains. It has been made more
  robust by taking care that :program:`nmbd` is started again before the main :program:`samba`
  daemon (:uv:bug:`55727`, :uv:bug:`55678`).

* In domains with larger numbers of users the command :command:`wbinfo -u` did not
  return any results (:uv:bug:`55962`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* Handling of rejects due to invalid pickle files has been repaired
  (:uv:bug:`55774`).

* The script :program:`resync_object_from_ucs.py` has an option ``--first`` which allows a
  particular DN or filtered list of DNs to be replicated with priority. This
  update fixes the sort order to actually put the DNs to the first position in
  the synchronization queue (:uv:bug:`55880`).

* If the system was upgraded from UCS 4.4 and had rejected objects the internal
  SQLite database was corrupted. The database will be repaired
  (:uv:bug:`54586`).

* The check for a running S4-Connector is now checking for Python 3 only
  processes (:uv:bug:`55632`).

* A translation for the MS group policy attribute has been added
  (:uv:bug:`55664`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* If the system was upgraded from UCS 4.4 and had rejected objects the internal
  SQLite database was corrupted. The database will be repaired
  (:uv:bug:`54587`).

* A server password change script for AD member mode has been moved from
  :program:`univention-ad-connector` to :program:`univention-role-server-common` to cover different
  use cases (:uv:bug:`55940`).

* Handling of rejects due to invalid pickle files has been repaired
  (:uv:bug:`55774`).

* The check for a running AD-Connector is now checking for Python 3 only
  processes (:uv:bug:`55632`).

* A new server password change script has been added for AD member mode
  (:uv:bug:`54390`).

.. _changelog-other:

*************
Other changes
*************

* ``Content-Security-Policy`` is removed from UCS realm init configuration, since it
  is handled by Apache configuration (:uv:bug:`55866`).

* This extension allows a group of people to reset the passwords of other
  users. Privileged users can be exempted, e.g. *Domain Admins*. The set of
  these users is stored in |UCSUCRV|
  :envvar:`ldap/acl/user/passwordreset/internal/groupmemberlist/`, but the ordering was
  not stable and could change on each invocation of :command:`ldap-group-to-file.py`.
  This lead to a restart of :command:`slapd`, which interrupted access to LDAP on a
  regular basis. This has been fixed by sorting the users and restarting
  :command:`slapd` only when the set of users changes (:uv:bug:`56099`).

* The scripts of :program:`univention-l10n` to manage translation are now executed with Python 3 instead of Python 2
  (:uv:bug:`55632`).

* Future compatibility with Python 3.11 has been added (:uv:bug:`55632`).

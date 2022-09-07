.. _relnotes-changelog:

#########################################################
Changelog for Univention Corporate Server (UCS) |release|
#########################################################

.. _changelog-general:

*******
General
*******

* Various unused Python 2 modules has been removed from the Debian packages
  (:uv:bug:`54706`).

* The server password change mechanism has been adjusted to
  first validate that the new machine password successfully replicated in
  OpenLDAP before finally changing the password locally in Samba/AD. Quickly
  reverting password changes in AD easily breaks DRS replication, so prevent
  this situation from happening (:uv:bug:`53205`).

.. _security:

* All security updates issued for UCS 5.0-1 are included:

  * :program:`apache2` (:uv:cve:`2021-44224`, :uv:cve:`2021-44790`)
    (:uv:bug:`54298`)

  * :program:`bind9` (:uv:cve:`2021-25220`) (:uv:bug:`54573`)

  * :program:`cifs-utils` (:uv:cve:`2022-27239`, :uv:cve:`2022-29869`)
    (:uv:bug:`54818`)

  * :program:`clamav` (:uv:cve:`2022-20698`) (:uv:bug:`54599`)

  * :program:`cups` (:uv:cve:`2020-10001`, :uv:cve:`2022-26691`)
    (:uv:bug:`54598`, :uv:bug:`54808`)

  * :program:`cyrus-sasl2` (:uv:cve:`2022-24407`) (:uv:bug:`54490`)

  * :program:`dpkg` (:uv:bug:`54810`)

  * :program:`expat` (:uv:cve:`2021-45960`, :uv:cve:`2021-46143`,
    :uv:cve:`2022-22822`, :uv:cve:`2022-22823`, :uv:cve:`2022-22824`,
    :uv:cve:`2022-22825`, :uv:cve:`2022-22826`, :uv:cve:`2022-22827`,
    :uv:cve:`2022-23852`, :uv:cve:`2022-23990`, :uv:cve:`2022-25235`,
    :uv:cve:`2022-25236`, :uv:cve:`2022-25313`, :uv:cve:`2022-25314`,
    :uv:cve:`2022-25315`) (:uv:bug:`54448`, :uv:bug:`54480`)

  * :program:`firefox-esr` (:uv:cve:`2021-4140`, :uv:cve:`2021-38503`,
    :uv:cve:`2021-38504`, :uv:cve:`2021-38506`, :uv:cve:`2021-38507`,
    :uv:cve:`2021-38508`, :uv:cve:`2021-38509`, :uv:cve:`2021-43534`,
    :uv:cve:`2021-43535`, :uv:cve:`2021-43536`, :uv:cve:`2021-43537`,
    :uv:cve:`2021-43538`, :uv:cve:`2021-43539`, :uv:cve:`2021-43541`,
    :uv:cve:`2021-43542`, :uv:cve:`2021-43543`, :uv:cve:`2021-43545`,
    :uv:cve:`2021-43546`, :uv:cve:`2022-1097`, :uv:cve:`2022-1196`,
    :uv:cve:`2022-1529`, :uv:cve:`2022-1802`, :uv:cve:`2022-22737`,
    :uv:cve:`2022-22738`, :uv:cve:`2022-22739`, :uv:cve:`2022-22740`,
    :uv:cve:`2022-22741`, :uv:cve:`2022-22742`, :uv:cve:`2022-22743`,
    :uv:cve:`2022-22745`, :uv:cve:`2022-22747`, :uv:cve:`2022-22748`,
    :uv:cve:`2022-22751`, :uv:cve:`2022-22754`, :uv:cve:`2022-22756`,
    :uv:cve:`2022-22759`, :uv:cve:`2022-22760`, :uv:cve:`2022-22761`,
    :uv:cve:`2022-22763`, :uv:cve:`2022-22764`, :uv:cve:`2022-24713`,
    :uv:cve:`2022-26381`, :uv:cve:`2022-26383`, :uv:cve:`2022-26384`,
    :uv:cve:`2022-26386`, :uv:cve:`2022-26387`, :uv:cve:`2022-26485`,
    :uv:cve:`2022-26486`, :uv:cve:`2022-28281`, :uv:cve:`2022-28282`,
    :uv:cve:`2022-28285`, :uv:cve:`2022-28286`, :uv:cve:`2022-28289`,
    :uv:cve:`2022-29909`, :uv:cve:`2022-29911`, :uv:cve:`2022-29912`,
    :uv:cve:`2022-29914`, :uv:cve:`2022-29916`, :uv:cve:`2022-29917`,
    :uv:cve:`2022-31736`, :uv:cve:`2022-31737`, :uv:cve:`2022-31738`,
    :uv:cve:`2022-31740`, :uv:cve:`2022-31741`, :uv:cve:`2022-31742`,
    :uv:cve:`2022-31747`) (:uv:bug:`54345`, :uv:bug:`54442`, :uv:bug:`54512`,
    :uv:bug:`54543`, :uv:bug:`54654`, :uv:bug:`54730`, :uv:bug:`54787`,
    :uv:bug:`54819`)

  * :program:`flac` (:uv:cve:`2020-0499`) (:uv:bug:`54608`)

  * :program:`ghostscript` (:uv:bug:`54314`)

  * :program:`gmp` (:uv:cve:`2021-43618`) (:uv:bug:`54602`)

  * :program:`gzip` (:uv:cve:`2022-1271`) (:uv:bug:`54672`)

  * :program:`intel-microcode` (:uv:cve:`2021-0127`, :uv:cve:`2021-0145`,
    :uv:cve:`2021-33120`) (:uv:bug:`54605`)

  * :program:`jbig2dec` (:uv:cve:`2020-12268`) (:uv:bug:`54610`)

  * :program:`libpcap` (:uv:cve:`2019-15165`) (:uv:bug:`54601`)

  * :program:`libxml2` (:uv:cve:`2022-23308`, :uv:cve:`2022-29824`)
    (:uv:bug:`54609`, :uv:bug:`54788`)

  * :program:`linux`, :program:`linux-latest`, :program:`linux-signed-amd64`,
    (:uv:cve:`2020-29374`, :uv:cve:`2020-36322`, :uv:cve:`2021-3640`,
    :uv:cve:`2021-3744`, :uv:cve:`2021-3752`, :uv:cve:`2021-3760`,
    :uv:cve:`2021-3764`, :uv:cve:`2021-3772`, :uv:cve:`2021-4002`,
    :uv:cve:`2021-4083`, :uv:cve:`2021-4135`, :uv:cve:`2021-4149`,
    :uv:cve:`2021-4155`, :uv:cve:`2021-4202`, :uv:cve:`2021-4203`,
    :uv:cve:`2021-20317`, :uv:cve:`2021-20321`, :uv:cve:`2021-20322`,
    :uv:cve:`2021-22600`, :uv:cve:`2021-28711`, :uv:cve:`2021-28712`,
    :uv:cve:`2021-28713`, :uv:cve:`2021-28714`, :uv:cve:`2021-28715`,
    :uv:cve:`2021-28950`, :uv:cve:`2021-38300`, :uv:cve:`2021-39685`,
    :uv:cve:`2021-39686`, :uv:cve:`2021-39698`, :uv:cve:`2021-39713`,
    :uv:cve:`2021-41864`, :uv:cve:`2021-42739`, :uv:cve:`2021-43389`,
    :uv:cve:`2021-43975`, :uv:cve:`2021-43976`, :uv:cve:`2021-44733`,
    :uv:cve:`2021-45095`, :uv:cve:`2021-45469`, :uv:cve:`2021-45480`,
    :uv:cve:`2022-0001`, :uv:cve:`2022-0002`, :uv:cve:`2022-0322`,
    :uv:cve:`2022-0330`, :uv:cve:`2022-0435`, :uv:cve:`2022-0487`,
    :uv:cve:`2022-0492`, :uv:cve:`2022-0617`, :uv:cve:`2022-0644`,
    :uv:cve:`2022-22942`, :uv:cve:`2022-23036`, :uv:cve:`2022-23037`,
    :uv:cve:`2022-23038`, :uv:cve:`2022-23039`, :uv:cve:`2022-23040`,
    :uv:cve:`2022-23041`, :uv:cve:`2022-23042`, :uv:cve:`2022-23960`,
    :uv:cve:`2022-24448`, :uv:cve:`2022-24958`, :uv:cve:`2022-24959`,
    :uv:cve:`2022-25258`, :uv:cve:`2022-25375`, :uv:cve:`2022-26966`)
    (:uv:bug:`54541`, :uv:bug:`54607`)

  * :program:`lxml` (:uv:cve:`2021-43818`) (:uv:bug:`54346`)

  * :program:`mariadb-10.3` (:uv:cve:`2021-35604`, :uv:cve:`2021-46659`,
    :uv:cve:`2021-46661`, :uv:cve:`2021-46662`, :uv:cve:`2021-46663`,
    :uv:cve:`2021-46664`, :uv:cve:`2021-46665`, :uv:cve:`2021-46667`,
    :uv:cve:`2021-46668`, :uv:cve:`2022-24048`, :uv:cve:`2022-24050`,
    :uv:cve:`2022-24051`, :uv:cve:`2022-24052`) (:uv:bug:`54604`)

  * :program:`nbd` (:uv:cve:`2022-26495`, :uv:cve:`2022-26496`)
    (:uv:bug:`54542`)

  * :program:`nss` (:uv:cve:`2022-22747`) (:uv:bug:`54375`)

  * :program:`ntfs-3g` (:uv:cve:`2021-46790`, :uv:cve:`2022-30783`,
    :uv:cve:`2022-30784`, :uv:cve:`2022-30785`, :uv:cve:`2022-30786`,
    :uv:cve:`2022-30787`, :uv:cve:`2022-30788`, :uv:cve:`2022-30789`)
    (:uv:bug:`54857`)

  * :program:`openldap` (:uv:cve:`2022-29155` ) (:uv:bug:`54627`,
    :uv:bug:`54783`)

  * :program:`openssl` (:uv:cve:`2021-4160`, :uv:cve:`2022-0778`,
    :uv:cve:`2022-1292`, :uv:cve:`2022-2068`) (:uv:bug:`54557`,
    :uv:bug:`54764`, :uv:bug:`54901`)

  * :program:`pillow` (:uv:cve:`2022-22815`, :uv:cve:`2022-22816`,
    :uv:cve:`2022-22817`) (:uv:bug:`54366`)

  * :program:`policykit-1` (:uv:cve:`2021-4034`) (:uv:bug:`54374`)

  * :program:`postgresql-11` (:uv:cve:`2022-1552`) (:uv:bug:`54751`)

  * :program:`rsyslog` (:uv:cve:`2019-17041`, :uv:cve:`2019-17042`,
    :uv:cve:`2022-24903`) (:uv:bug:`54600`, :uv:bug:`54809`)

  * :program:`samba` (:uv:cve:`2021-43566`, :uv:cve:`2021-44142`,
    :uv:cve:`2022-0336`) (:uv:bug:`53629`, :uv:bug:`54015`, :uv:bug:`54200`,
    :uv:bug:`54278`, :uv:bug:`54369`)

  * :program:`squid` (:uv:cve:`2021-28116`, :uv:cve:`2021-46784`)
    (:uv:bug:`54907`)

  * :program:`tiff` (:uv:cve:`2022-0561`, :uv:cve:`2022-0562`,
    :uv:cve:`2022-0865`, :uv:cve:`2022-0891`, :uv:cve:`2022-0907`,
    :uv:cve:`2022-0908`, :uv:cve:`2022-0909`, :uv:cve:`2022-0924`,
    :uv:cve:`2022-22844`) (:uv:bug:`54595`)

  * :program:`vim` (:uv:cve:`2019-20807`, :uv:cve:`2021-3770`,
    :uv:cve:`2021-3778`, :uv:cve:`2021-3796`) (:uv:bug:`54606`)

  * :program:`xorg-server` (:uv:cve:`2021-4008`, :uv:cve:`2021-4009`,
    :uv:cve:`2021-4010`, :uv:cve:`2021-4011`) (:uv:bug:`54270`)

  * :program:`xterm` (:uv:cve:`2022-24130`) (:uv:bug:`54603`)

  * :program:`xz-utils` (:uv:cve:`2022-1271`) (:uv:bug:`54671`)

  * :program:`zlib` (:uv:cve:`2018-25032`) (:uv:bug:`54631`)

.. _debian:

* The following updated packages from Debian 10.12 are included
  (:uv:bug:`54866`): :program:`aide`, :program:`apache-log4j1.2`,
  :program:`apache-log4j2`, :program:`atftp`, :program:`base-files`,
  :program:`beads`, :program:`btrbk`, :program:`cargo-mozilla`,
  :program:`chrony`, :program:`cimg`, :program:`condor`,
  :program:`debian-edu-config`, :program:`debian-installer-netboot-images`,
  :program:`debian-installer`, :program:`detox`, :program:`djvulibre`,
  :program:`ecdsautils`, :program:`evolution-data-server`, :program:`exo`,
  :program:`faad2`, :program:`ffmpeg`, :program:`firejail`, :program:`gerbv`,
  :program:`glibc`, :program:`graphicsmagick`, :program:`h2database`,
  :program:`htmldoc`, :program:`http-parser`, :program:`icu`,
  :program:`ipython`, :program:`jtharness`, :program:`jtreg`,
  :program:`lemonldap-ng`, :program:`leptonlib`,
  :program:`libdatetime-timezone-perl`, :program:`libencode-perl`,
  :program:`libetpan`, :program:`libextractor`, :program:`libjackson-json-java`,
  :program:`libmodbus`, :program:`libphp-adodb`, :program:`librecad`,
  :program:`libsdl1.2`, :program:`lighttpd`, :program:`llvm-toolchain-11`,
  :program:`lrzip`, :program:`lxcfs`, :program:`mailman`, :program:`mediawiki`,
  :program:`modsecurity-apache`, :program:`needrestart`,
  :program:`node-getobject`, :program:`openjdk-11`, :program:`openscad`,
  :program:`opensc`, :program:`php-illuminate-database`,
  :program:`phpliteadmin`, :program:`plib`, :program:`privoxy`,
  :program:`prosody`, :program:`publicsuffix`, :program:`python-bottle`,
  :program:`python-virtualenv`, :program:`raptor2`, :program:`redis`,
  :program:`ros-ros-comm`, :program:`roundcube`, :program:`ruby2.5`,
  :program:`ruby-httpclient`, :program:`rust-cbindgen`,
  :program:`rustc-mozilla`, :program:`smarty3`, :program:`snapd`,
  :program:`sogo`, :program:`sphinxsearch`, :program:`spip`,
  :program:`strongswan`, :program:`subversion`, :program:`thunderbird`,
  :program:`trafficserver`, :program:`tryton-proteus`, :program:`tryton-server`,
  :program:`tzdata`, :program:`uriparser`, :program:`usbview`,
  :program:`varnish`, :program:`vlc`, :program:`waitress`, :program:`wavpack`,
  :program:`webkit2gtk`, :program:`weechat`, :program:`wireshark`,
  :program:`wordpress`, :program:`zsh`, :program:`zziplib`,

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:
  :program:`python-jose` (:uv:bug:`54666`), :program:`python-keycloak`
  (:uv:bug:`54689`), :program:`univention-support-info`, (:uv:bug:`53358`)

.. _changelog-installer:

********************
Univention Installer
********************

* Remove left-over static host configuration for ``127.0.1.1``
  (:uv:bug:`49042`).

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

* Adapted the code due to a Linux kernel API change in *v5.7-rc1~128*, where
  :func:`open(O_EXCL) <open>` now returns ``EEXIST``, instead of ``EISDIR``
  (:uv:bug:`54476`).

* The remaining scripts have all been migrated to Python 3 (:uv:bug:`54208`).

* The Python-API of |UCSUCR| has been extended to offer a method
  :func:`get_int`, that can be used to avoid receiving a string, when an integer
  is required. If the value of the requested |UCSUCRV| is not a number, the
  default value is returned verbatim instead (:uv:bug:`20933`).

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* The |UCSUCR| template for the file :file:`/etc/hosts`, now always produces the
  same output given the same configuration (:uv:bug:`54558`).

* Clarified the description of the |UCSUCRV| :envvar:`logrotate/rotate/count`
  (:uv:bug:`54691`).

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-domain-openldap:

OpenLDAP
========

* The ``ppolicy`` overlay module uses embedded Python. This has been migrated to
  Python 3 (:uv:bug:`54582`).

* The behavior of the ``translog`` overlay was modified to skip grandchildren of
  the ``cn=temporary,cn=univention``, container. This new behavior can be
  controlled by the |UCSUCRV| :envvar:`ldap/translog-ignore-temporary`. This
  reduces the number of replication transactions during creation of users and
  groups significantly. As a result it increases the replication performance and
  reduces the rate at which the ``cn=translog`` LMDB backend database gets
  filled. This variable is applicable only to the |UCSPRIMARYDN|. The package
  :program:`univention-ldap-server` activates this variable by default
  (:uv:bug:`48626`).

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* An error when deactivating a listener module through UCR has been fixed
  (:uv:bug:`54696`).

* :samp:`univention-translog import --min {TID}` had no effect
  (:uv:bug:`54794`).

* Several memory issues have been fixed (:uv:bug:`49868`).

* The Notifier sometimes failed to process all transaction in bulk and aborted.
  This lead to the Notifier making no progress and filling the log file with the
  same error messages again and again. Transactions are now processes
  incrementally (:uv:bug:`49868`).

* If the number of transactions was lower than 1000, only a partial number of
  transactions has been imported during the join of a backup (:uv:bug:`54203`).

.. _changelog-domain-dnsserver:

DNS server
==========

* The |UCSUCRV| :envvar:`dns/timeout-start` is now also considered in the
  :file:`systemd` unit :file:`univention-bind-ldap`. This can be used in cases
  where a large number of DNS zones slows down the start of the DNS server bind.
  This only affects systems which have :envvar:`dns/backend` set to ``ldap``.
  i.e. systems that are not configured as Samba/AD DC. After changing the
  variable, running :command:`systemctl daemon-reload` once is required
  (:uv:bug:`54108`).

.. _changelog-domain-listener:

Univention Directory Listener
=============================

* The unused method :py:func:`get_configuration` has been removed from the
  :py:class:`~univention.listener.handler_configuration.ListenerModuleConfiguration`
  class in the :py:mod:`univention.listener.handler_configuration` module
  (:uv:bug:`54501`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* A new widget suggesting mail domains while typing has been introduced
  (:uv:bug:`54467`).

* The logic for mapping UDM syntax classes to UMC front end widgets and to get
  the dynamic choices for a UDM syntax have been moved into the UDM syntax
  classes (:uv:bug:`38762`).

* The domain component in an LDAP path is not shown in wrong reversed order
  anymore (:uv:bug:`53678`).

* In case of a long-lasting login, certain UMC modules do not work properly. If
  this happens, a message will be displayed to the user containing a link to
  :uv:kb:`6413` (:uv:bug:`54032`).

* A new method has been added to generate and set a service specific password
  for a user (:uv:bug:`54438`).

* The UDM REST API now supports UDM object types containing ``-`` in their name
  (:uv:bug:`54063`).

* The ``entryUUID`` and ``dn`` of newly created objects are now included in the
  response (:uv:bug:`54347`).

* The UDM REST API now supports multiprocessing via the |UCSUCRV|
  :envvar:`directory/manager/rest/processes`. Further details can be found in
  the performance guide (:uv:bug:`50050`).

.. _changelog-umc-portal:

Univention Portal
=================

* The Portal server now fetches user information from the UMC server
  asynchronously (:uv:bug:`53853`).

* Fixed various accessibility issues (:uv:bug:`54556`).

* Fixed various CSS issues (:uv:bug:`54556`).

* Added new tooltips. They comply with accessibility requirements
  (:uv:bug:`54556`).

* Improved the translation widget when editing portal entries (:uv:bug:`54556`).

* Fixed drag and drop behavior when using the keyboard, added screen reader
  support (:uv:bug:`54556`).

* The portal now integrates the self service functionality: Reset passwords,
  change profile, verify accounts, etc is now possible from within the portal
  (:uv:bug:`54556`).

* The French translation of UDM portal attributes has been updated
  (:uv:bug:`54029`).

* Some requests have been excluded from :envvar:`apache2/force_https`, so that
  the portal tiles in the UMC are shown even if https is forced
  (:uv:bug:`53296`).

* The Portal server now provides a navigation endpoint (:uv:bug:`54618`).

* Keywords can now be added to portal entries. They are not visible, but
  searchable (:uv:bug:`54295`).

* Entries can now be opened in new tabs with a specific internal name ("target")
  (:uv:bug:`54633`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* The function :py:func:`DNSanitizer` has been added to the Python module
  variable ``__all__`` to prevent warnings for developers (:uv:bug:`52445`).

* The cookie attribute ``SameSite`` can now be set for UMC cookies via the
  |UCSUCRV| :envvar:`umc/http/cookie/samesite` (:uv:bug:`54484`).

* :program:`univention-management-console-dev` now depends on both
  :program:`imagemagick` and :program:`inkscape` (:uv:bug:`54043`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* The reason why servers are excluded from the app-installation drop-down menu
  is displayed again (:uv:bug:`54460`).

* Change order and prioritize App specific settings over App Center settings
  when populating the environment file. This is required for some upcoming Apps
  to be installed (:uv:bug:`54612`).

* Allow for the ``tmpfs``, that are created for a docker app to be defined in
  the apps ini file (:uv:bug:`54562`).

* A race condition was fixed, that caused apps to lose their installation status
  (:uv:bug:`54452`).

* Validate the form when choosing the installation host (:uv:bug:`53523`).

* Make the check regarding network conflicts with docker more robust
  (:uv:bug:`54082`).

.. _changelog-umc-udmcli:

|UCSUDM| UMC modules and command line interface
===============================================

* The mapping of syntax class to UMC widgets via the |UCSUCRV|
  :envvar:`directory/manager/web/widget/.*` has been removed. This can now be
  achieved via syntax classes directly (:uv:bug:`54840`).

* An error introduced in :uv:erratum:`5.0x335` has been repaired which caused
  that e.g. the selection list of printer model in the printer shares module
  could not be fetched (:uv:bug:`54849`).

* The error handling of the syntax class ``jpegPhoto`` was broken since UCS
  5.0-0 and has been repaired (:uv:bug:`54769`).

* Clarified error message for invalid host name or FQDN (:uv:bug:`54663`).

* The available mail domains are now suggested when entering values for the
  attribute ``mailPrimaryAddress`` of objects ``users/user`` (:uv:bug:`54467`).

* Syntax classes can now depend on another UDM property and restrict their
  choices based on that (:uv:bug:`53843`).

* The logic for mapping UDM syntax classes to UMC front end widgets and to get
  the dynamic choices for a UDM syntax have been moved into the UDM syntax
  classes (:uv:bug:`38762`).

* A crash while accessing an user with multiple user certificates has been
  repaired (:uv:bug:`54617`).

* Changing the case of the name or email attributes will no longer be prevented
  by the locking mechanism (:uv:bug:`52760`).

* Some redundant log messages logging password hashes were removed
  (:uv:bug:`54348`).

* The performance of the license check has been improved to reduce the initial
  login time (:uv:bug:`52292`).

* Backend functionality for service specific passwords has been added. It cannot
  be used via CLI (:uv:bug:`54438`).

* When removing a policy the policy is removed from the referencing objects
  (:uv:bug:`16966`).

* Searching with patterns containing umlauts is possible again
  (:uv:bug:`53975`).

* It is now possible to search for the user expiry date of ``users/user``
  objects (:uv:bug:`54150`).

* Two resource sharing conflicts on Python dictionaries have been fixed, that
  could lead to tracebacks when modules are reloaded in a multi-threaded context
  (:uv:bug:`53581`).

* Moving of ``users/ldap`` objects is possible again. This was broken due to the
  Python 3 migration in UCS 5.0 (:uv:bug:`54085`).

* When user templates were members of groups an error was raised which prevented
  opening or modifying that group. Templates as group members are now ignored in
  UDM module ``groups/group``, (:uv:bug:`54402`).

* When setting an user as a member of a group in UDM, that had the same UID but
  a different DN of another member, the related attribute ``memberUid`` of the
  group got dropped. This happened in the cool Solution user-group-sync during
  move operations (:uv:bug:`54297`).

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

* The ``entryUUID`` of an LDAP object is now exposed by the UDM API
  (:uv:bug:`54883`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* The package :program:`univention-system-setup` has been migrated to Python 3
  (:uv:bug:`51318`).

.. _changelog-umc-join:

Domain join module
==================

* When executing join scripts via UMC module ``Domain Join`` the progress bar
  will now display the name of the currently running script instead of the last
  script that was finished (:uv:bug:`33255`).

* The joinscript of :program:`univention-samba4` did pass the credentials in
  clear text to other tools like :command:`ldbsearch` as command line arguments.
  To reduce the attack surface it now uses a file instead (:uv:bug:`53100`).

* Joining a backup node into a single server UCS@school environment failed
  because the LDB module :file:`univention_samaccountname_ldap_check`, attempted
  to create an object of type ``computers/windows`` for it which always failed
  because the account name was already taken by the
  ``computers/domaincontroller_backup`` object (:uv:bug:`54768`).

* Several memory and open file descriptor leaks have been fixed. An error
  restarting Samba during package installation has been fixed. The build system
  for the package has been cleaned up (:uv:bug:`48823`).

.. _changelog-umc-reports:

Univention Directory Reports
============================

* The script :command:`univention-directory-reports` now offers two new options:
  The option ``--output-dir`` allows specification of the output directory and
  ``--output-name`` allows to specify the file name of the report
  (:uv:bug:`54153`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* A new diagnostic plugin has been added to detect cases where the group
  membership attributes ``uniqueMember`` and ``memberUid`` are no longer
  consistent (:uv:bug:`48652`).

* :file:`52_mail_acl_sync` will no longer fail if multiple IMAP mail folders
  exist (:uv:bug:`54675`).

* A new diagnostic plugin has been added to detect cases where an LDAP schema is
  missing that is actually still referenced by some objects (:uv:bug:`53455`).

* The script :command:`univention-run-diagnostic-check` now displays links in
  the description of failed tests (:uv:bug:`50756`).

* Disk usage checks will now handle log level evaluations of |UCSUCRV|
  :envvar:`ldap/debug/level` correctly (:uv:bug:`49354`).

* A diagnostic warning for the Samba replication status will now be formatted
  properly (:uv:bug:`53341`).

* Mounted ISO images are no longer included in the disk usage diagnostic plugin
  (:uv:bug:`49353`).

* The Python 3 compatibility when handling exceptions in certain diagnostic
  plugins has been corrected (:uv:bug:`53306`).

* A diagnostic module has been added to check the |UCSUCRV|
  :envvar:`notifier/protocol/version`, (:uv:bug:`54264`).

* :command:`univention-run-diagnostic-checks` now offers to run a group of tests
  and also to exclude some of the tests (:uv:bug:`53969`).

* The script :command:`univention-run-diagnostic-check` is now executed with
  machine account credentials by default (:uv:bug:`54515`).

* The detection of :command:`slapschema` error message has been improved in
  :command:`62_check_slapschema`, (:uv:bug:`54681`).

.. _changelog-umc-quota:

File system quota module
========================

* Setting quotas for accounts with a fully numeric username has been fixed
  (:uv:bug:`54638`).

.. _changelog-umc-other:

Other modules
=============

* Syntax classes can now depend on another UDM property and restrict their
  choices based on that (:uv:bug:`53843`).

* The logic for mapping UDM syntax classes to UMC front end widgets and to get
  the dynamic choices for a UDM syntax have been moved into the UDM syntax
  classes (:uv:bug:`38762`).

* A UMC operation set enabling the creation of UDM Reports was added
  (:uv:bug:`54109`).

* Byte values are now correctly decoded for the labels of choices delivered by
  the syntax class ``LDAP_Search``, (:uv:bug:`54190`).

* The domain component in a LDAP path is not shown in wrong reversed order
  anymore (:uv:bug:`53678`).

* The |UCSUCRV|
  :envvar:`directory/manager/web/modules/users/user/wizard/property/
  invite/default` will now work properly and can be used to activate the
  :guilabel:`invite user via e-mail` option in the user wizard by default
  (:uv:bug:`54316`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* Detecting UMC specific files did not work for packages having files, which
  have blanks in their filenames. This lead to error messages during package
  upgrades and inconsistent cache behavior (:uv:bug:`54047`).

* ``UCSVersion`` not includes the erroneous input parameter is included in the
  error message for debugging (:uv:bug:`49061`).

* Added the new function :func:`generate_password` that can generate random
  passwords. The new function :func:`password_config` can be used to get
  parameters for that from UCR (:uv:bug:`54555`).

* Changing a user password is now possible again when the referenced password
  history policy did not define values for password length or history length
  (:uv:bug:`51354`).

* For :program:`Python-ldap-3.3.0` (and higher) some TLS settings are no longer
  immediately materialized. To ensure correct behavior of TLS encrypted LDAP
  connections, the option ``OPT_X_TLS_NEWCTX`` will be necessary for future UCS
  versions (:uv:bug:`54408`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* :command:`univention-upgrade --updateto` is parsed earlier and exits on wrong
  parameter (:uv:bug:`49061`).

* :command:`apt-get --force-yes` option is deprecated and has been replaced with
  ``--allow-unauthenticated``, ``--allow-downgrades``
  ``--allow-remove-essential``, ``--allow-change-held-packages``
  (:uv:bug:`48891`).

* App updates invoked by :command:`univention-upgrade` will now work correctly
  (:uv:bug:`53666`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-postgresql:

PostgreSQL
==========

* During the upgrade to UCS 5.0-1 PostgreSQL 11 might have been disabled by
  setting the |UCSUCRV| :envvar:`postgres11/autostart=no` by accident
  (:uv:bug:`54255`).

.. _changelog-service-docker:

Docker
======

* The script :command:`migrate_container_MountPoints_to_v2_config` is deprecated
  since UCS 4.3 and has been removed (:uv:bug:`52539`).

* The package :program:`univention-docker-container-mode` is deprecated since
  UCS 4.3 and has been replaced by an empty transitional package
  (:uv:bug:`52539`).

.. _changelog-service-saml:

SAML
====

* The cookie attributes ``Secure`` and ``SameSite`` can now be set for the
  session and language cookies of SAML Identity Providers via |UCSUCRV|
  :envvar:`saml/idp/session-cookie/secure`,
  :envvar:`saml/idp/session-cookie/samesite`,
  :envvar:`saml/idp/language-cookie/secure` and
  :envvar:`saml/idp/language-cookie/samesite`, (:uv:bug:`54483`).

* The link to the self service has been changed to point to the new portal based
  self service (:uv:bug:`54556`).

* An internal ID has been fixed, which caused the German translation not being
  shown when new passwords did not match (:uv:bug:`54268`).

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

.. _changelog-service-selfservice:

Univention self service
=======================

* The logic for mapping UDM syntax classes to UMC front end widgets and to get
  the dynamic choices for a UDM syntax have been moved into the UDM syntax
  classes (:uv:bug:`38762`).

* The Self Service now adds its dedicated portal to make use of the new features
  in Univention Portal. For more, see :uv:help:`19671` (:uv:bug:`54556`).

* A new backend function has been added that can set service specific passwords
  for a user (:uv:bug:`54434`).

* The e-mail template for password reset tokens now support additional
  placeholders for the properties ``title``, ``initials``, ``displayName``,
  ``firstname``, ``lastname``, ``mailPrimaryAddress``,
  ``employeeNumber`` and ``organisation`` (:uv:bug:`48960`).

* The package has been migrated to Python 3. Custom plugins for sending the
  password recovery tokens also need to be migrated to Python 3
  (:uv:bug:`51327`, :uv:bug:`54466`).

* The French translation of UDM extended attributes and portal attributes has
  been updated (:uv:bug:`54029`).

.. _changelog-service-mail:

Mail services
=============

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

* A bug where antivirus signatures could not get updated properly on fresh
  installations has been fixed (:uv:bug:`54070`).

.. _changelog-service-dovecot:

Dovecot
=======

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

.. _changelog-service-postfix:

Postfix
=======

* Error handling in the script
  :file:`/usr/share/univention-mail-postfix/listfilter.py`, has been repaired
  (:uv:bug:`54560`).

.. _changelog-service-monitoring:

Monitoring / Nagios
===================

* A new monitoring system has been implemented based on :program:`Prometheus`,
  :program:`Prometheus Alertmanager` and :program:`Grafana`. During the upgrade
  all current Nagios services are migrated to Monitoring alerts
  (:uv:bug:`54748`, :uv:bug:`54749`, :uv:bug:`54750`).

* The configuration of NRPE plugin definitions was broken due to the migration
  to Python 3 and has been repaired (:uv:bug:`53681`).

* The Nagios plugins in :program:`univention-nagios-client`, have been converted
  to Python 3 (:uv:bug:`52258`).

.. _changelog-service-apache:

Apache
======

* Apache can now be configured to only support TLS v1.3 connections by setting
  the |UCSUCRV| :envvar:`ucr set apache2/ssl/tlsv13=true`, (:uv:bug:`54306`).

.. _changelog-service-radius:

RADIUS
======

* The RADIUS server can now assign VLAN IDs to user connections if their group
  has set the attribute ``vlanId``. The |UCSUCRV| :envvar:`freeradius/vlan-id`
  has been added to set a VLAN ID even if the user is no member of any such
  group (:uv:bug:`25916`).

* A new |UCSUCRV| :envvar:`radius/use-service-specific-passwords.` has been
  added: If enabled, the authentication is done against a RADIUS specific
  password, not the domain password of the user (:uv:bug:`54409`).

* An error while adding the French translation to an extended attribute during
  the package update has been fixed (:uv:bug:`54461`).

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

* Updating an old RADIUS installation will now correctly update the description
  for the extended attributes ``networkAccessGroups`` and
  ``NetworkAccessComputers``, (:uv:bug:`54341`).

.. _changelog-service-proxy:

Proxy services
==============

* The package :program:`univention-squid` has been migrated to Python 3
  (:uv:bug:`53357`).

.. _changelog-service-kerberos:

Kerberos
========

* The Kerberos ticket lifetime was made configurable via |UCSUCRV|
  :envvar:`kerberos/defaults/ticket-lifetime`, (:uv:bug:`52987`).

.. _changelog-service-ssl:

SSL
===

* Some web browsers refused wildcard certificates generated by
  :command:`univention-certificates` because the information was only stored in
  ``common name`` but required in ``subject alternative names``, too
  (:uv:bug:`53288`).

.. _changelog-service-dhcp:

DHCP server
===========

* Add UCR packages to profile for network installation (:uv:bug:`54259`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* Samba has been updated to version 4.16.2 (:uv:bug:`54682`).

* In some cases, in UCS@school the :file:`log.smbd`, filled with a message
  because a Windows 10 client attempted to access user files, which is denied by
  the NTACLs. While the origin of that behavior is still unknown, no negative
  side effects are known. To avoid overflowing the log file, we adjusted the log
  message to only start appearing at the debug level 2. Default log level is 1
  (:uv:bug:`52979`).

* :command:`samba-tool` now supports passing credentials using the option
  ``--authentication-file`` and the machine password using the option
  ``--machinepass-file`` (:uv:bug:`53101`).

* The share configuration of ``vfs objects``, ``write list``, ``hosts allow``
  and ``hosts deny`` was broken because of too excessive escaping of quotes and
  has been repaired (:uv:bug:`49842`).

* The share setting ``map acl inherit = yes`` has been broken since UCS 5.0-0
  and is not working properly again (:uv:bug:`54688`).

* The access to home shares via NTLM authentication on UCSMEMBER has been fixed
  (:uv:bug:`54200`).

* The joinscript of :program:`univention-samba4` did pass the credentials in
  clear text to other tools like :command:`ldbsearch` as command line arguments.
  To reduce the attack surface it now uses a file instead (:uv:bug:`53100`).

* During a server password change the Samba process was not restarted in some
  cases. The script to restart Samba was fixed to ensure the service is
  restarted successfully (:uv:bug:`54356`).

* The Kerberos ticket lifetime was made configurable via |UCSUCRV|
  :envvar:`kerberos/defaults/ticket-lifetime`, (:uv:bug:`52987`).

.. _changelog-win-takeover:

Univention AD Takeover
======================

* :command:`samba-tool` now supports passing machine password using the option
  ``--machinepass-file`` (:uv:bug:`53101`).

* :command:`samba-tool` now supports passing credentials using the options ``-A
  | --authentication-file`` (:uv:bug:`53101`).

* Performing an Active Directory takeover will work when the original AD
  contains Group Policy Objects that use non ASCII encoding (:uv:bug:`54196`).

* Invalid (empty) UCR network interface configuration lead to network failure
  during AD Takeover (:uv:bug:`54359`).

* On systems updated from UCS 4.4 the AD-Takeover could abort with a traceback
  because the :command:`systemctl` command was not found under the path
  specified in the Python code (:uv:bug:`54238`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* The user expiry was off by one day between UCS and Samba. This discrepancy has
  been removed (:uv:bug:`53012`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* For :program:`Python-ldap-3.3.0` (and higher) some TLS settings are no longer
  immediately materialized. To ensure correct behavior of TLS encrypted LDAP
  connections, the option ``OPT_X_TLS_NEWCTX`` will be necessary for future UCS
  versions (:uv:bug:`54408`).

.. _changelog-other:

*************
Other changes
*************

* Improve message consistency between the man page and the ``--help``
  messages (:uv:bug:`54588`).

* Fix spelling mistake of :command:`rsync` in :file:`doc/univention-ssh.8`,
  (:uv:bug:`54588`).

* Update the :command:`univention-scp --help` and :command:`univention-rsync`
  message to specify that the ``--no-split`` option must be set before the
  password file parameter (:uv:bug:`54588`).

* Added support for `RFC6265bis <https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis-10>`_
  *SameSite* cookie attribute (:uv:bug:`54483`).

* Fixed Python 2 compatibility of UCR template
  :file:`slapd.conf.d/65admingrp-user-passwordreset`, introduced by
  :uv:erratum:`5.0x308` (:uv:bug:`54790`).

* The start of OpenLDAP could fail if the ACL lines got too long. This could
  happen if the |UCSUCRV| :envvar:`ldap/acl/user/passwordreset/.*` have a lot of
  values (:uv:bug:`54744`).

* The group membership cache now returns an empty list instead of None when
  requesting non-existing keys. This fixes a traceback in the Microsoft 365
  connector listener, when not every ``ADConnectionAlias`` has at least one user
  (:uv:bug:`54572`).

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

* A new attribute ``univentionRadiusPassword`` has been added to the user class
  (:uv:bug:`54395`).

* The French translation of UDM extended attributes has been updated
  (:uv:bug:`54029`).

* A new |UCSUCRV| :envvar:`ldap/translog-ignore-temporary` has been created to
  control if UDM temporary objects should be considered for replication by the
  OpenLDAP :file:`translog`, overlay which feeds the Listener/Notifier. This
  reduces the number of replication transactions during creation of users and
  groups significantly. As a result it increases the replication performance and
  reduces the rate at which the ``cn=translog`` LMDB backend database gets
  filled. This variable is applicable only to the |UCSPRIMARYDN|. By default is
  will be set to ``yes``, during package installation and update
  (:uv:bug:`48626`).

* A new LDAP attribute has been introduced with :uv:erratum:`5.0x100`. As
  re-indexing is time consuming the decision was made to delay the indexing
  until 5.0-2 and not to do it via an errata update. Therefore, a manual fix for
  customers is available and the required steps are documented at
  :uv:help:`19248` (:uv:bug:`54092`).

* The French translation package has been given a comprehensive update to align
  it to the current source code. All missing translation strings have been added
  and all outdated ones updated along with some general improvements of existing
  translation strings (:uv:bug:`54029`).

* Bugs in the localization template files were updated to fix the creation and
  update process of language packages (:uv:bug:`54029`).


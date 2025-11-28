.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
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

* |UCSUCS| |release| includes all security updates issued for UCS 5.2-3:

  * :program:`amd64-microcode` (:uv:cve:`2024-56161`)
    (:uv:bug:`58597`)

  * :program:`apache2` (:uv:cve:`2024-42516`, :uv:cve:`2024-43204`,
    :uv:cve:`2024-43394`, :uv:cve:`2024-47252`, :uv:cve:`2025-23048`,
    :uv:cve:`2025-49630`, :uv:cve:`2025-49812`, :uv:cve:`2025-53020`,
    :uv:cve:`2025-54090`) (:uv:bug:`58601`)

  * :program:`bind9` (:uv:cve:`2025-40778`, :uv:cve:`2025-40780`,
    :uv:cve:`2025-8677`) (:uv:bug:`58742`)

  * :program:`clamav` (:uv:cve:`2025-20128`, :uv:cve:`2025-20260`)
    (:uv:bug:`58593`)

  * :program:`cloud-init` (:uv:cve:`2024-11584`, :uv:cve:`2024-6174`)
    (:uv:bug:`58611`)

  * :program:`cups` (:uv:cve:`2025-58060`, :uv:cve:`2025-58364`)
    (:uv:bug:`58641`)

  * :program:`curl` (:uv:cve:`2023-27534`, :uv:cve:`2024-11053`,
    :uv:cve:`2024-9681`, :uv:cve:`2025-0167`) (:uv:bug:`58618`)

  * :program:`djvulibre` (:uv:cve:`2021-46310`, :uv:cve:`2021-46312`,
    :uv:cve:`2025-53367`) (:uv:bug:`58614`)

  * :program:`expat` (:uv:cve:`2023-52425`, :uv:cve:`2024-50602`,
    :uv:cve:`2024-8176`) (:uv:bug:`58598`)

  * :program:`fig2dev` (:uv:cve:`2025-46397`, :uv:cve:`2025-46398`,
    :uv:cve:`2025-46399`, :uv:cve:`2025-46400`) (:uv:bug:`58710`)

  * :program:`firefox-esr` (:uv:cve:`2025-10527`,
    :uv:cve:`2025-10528`, :uv:cve:`2025-10529`, :uv:cve:`2025-10532`,
    :uv:cve:`2025-10533`, :uv:cve:`2025-10536`, :uv:cve:`2025-10537`,
    :uv:cve:`2025-11708`, :uv:cve:`2025-11709`, :uv:cve:`2025-11710`,
    :uv:cve:`2025-11711`, :uv:cve:`2025-11712`, :uv:cve:`2025-11714`,
    :uv:cve:`2025-11715`, :uv:cve:`2025-13012`, :uv:cve:`2025-13013`,
    :uv:cve:`2025-13014`, :uv:cve:`2025-13015`, :uv:cve:`2025-13016`,
    :uv:cve:`2025-13017`, :uv:cve:`2025-13018`, :uv:cve:`2025-13019`,
    :uv:cve:`2025-13020`) (:uv:bug:`58651`, :uv:bug:`58723`,
    :uv:bug:`58812`)

  * :program:`ghostscript` (:uv:cve:`2025-59798`,
    :uv:cve:`2025-59799`, :uv:cve:`2025-7462`) (:uv:bug:`58709`)

  * :program:`glib2.0` (:uv:cve:`2025-3360`, :uv:cve:`2025-4373`,
    :uv:cve:`2025-7039`) (:uv:bug:`58613`)

  * :program:`glibc` (:uv:cve:`2025-0395`, :uv:cve:`2025-4802`,
    :uv:cve:`2025-8058`) (:uv:bug:`58622`)

  * :program:`imagemagick` (:uv:cve:`2025-43965`,
    :uv:cve:`2025-53014`, :uv:cve:`2025-53019`, :uv:cve:`2025-53101`,
    :uv:cve:`2025-55154`, :uv:cve:`2025-55212`, :uv:cve:`2025-55298`,
    :uv:cve:`2025-57803`, :uv:cve:`2025-57807`) (:uv:bug:`58639`)

  * :program:`intel-microcode` (:uv:cve:`2025-20053`,
    :uv:cve:`2025-20109`, :uv:cve:`2025-21090`, :uv:cve:`2025-22839`,
    :uv:cve:`2025-22840`, :uv:cve:`2025-22889`, :uv:cve:`2025-24305`,
    :uv:cve:`2025-26403`, :uv:cve:`2025-32086`) (:uv:bug:`58746`)

  * :program:`jinja2` (:uv:cve:`2024-56201`, :uv:cve:`2024-56326`,
    :uv:cve:`2025-27516`) (:uv:bug:`58596`)

  * :program:`krb5` (:uv:cve:`2024-26462`, :uv:cve:`2025-24528`,
    :uv:cve:`2025-3576`) (:uv:bug:`58612`)

  * :program:`lasso` (:uv:cve:`2025-46404`, :uv:cve:`2025-46705`,
    :uv:cve:`2025-47151`) (:uv:bug:`58813`)

  * :program:`libarchive` (:uv:cve:`2025-5914`, :uv:cve:`2025-5915`,
    :uv:cve:`2025-5916`, :uv:cve:`2025-5917`) (:uv:bug:`58615`)

  * :program:`libcap2` (:uv:cve:`2025-1390`) (:uv:bug:`58623`)

  * :program:`libcpanel-json-xs-perl` (:uv:cve:`2025-40929`)
    (:uv:bug:`58640`)

  * :program:`libfcgi` (:uv:cve:`2025-23016`) (:uv:bug:`58625`)

  * :program:`libjson-xs-perl` (:uv:cve:`2025-40928`)
    (:uv:bug:`58643`)

  * :program:`libsndfile` (:uv:cve:`2022-33065`, :uv:cve:`2024-50612`)
    (:uv:bug:`58606`)

  * :program:`libyaml-libyaml-perl` (:uv:cve:`2025-40908`)
    (:uv:bug:`58604`)

  * :program:`linux` (:uv:cve:`2024-36331`, :uv:cve:`2024-47704`,
    :uv:cve:`2024-57924`, :uv:cve:`2024-58240`, :uv:cve:`2025-21861`,
    :uv:cve:`2025-23143`, :uv:cve:`2025-23160`, :uv:cve:`2025-37925`,
    :uv:cve:`2025-37931`, :uv:cve:`2025-37968`, :uv:cve:`2025-38322`,
    :uv:cve:`2025-38335`, :uv:cve:`2025-38347`, :uv:cve:`2025-38491`,
    :uv:cve:`2025-38500`, :uv:cve:`2025-38501`, :uv:cve:`2025-38502`,
    :uv:cve:`2025-38520`, :uv:cve:`2025-38552`, :uv:cve:`2025-38553`,
    :uv:cve:`2025-38555`, :uv:cve:`2025-38560`, :uv:cve:`2025-38561`,
    :uv:cve:`2025-38562`, :uv:cve:`2025-38563`, :uv:cve:`2025-38565`,
    :uv:cve:`2025-38569`, :uv:cve:`2025-38572`, :uv:cve:`2025-38574`,
    :uv:cve:`2025-38576`, :uv:cve:`2025-38577`, :uv:cve:`2025-38578`,
    :uv:cve:`2025-38579`, :uv:cve:`2025-38581`, :uv:cve:`2025-38583`,
    :uv:cve:`2025-38587`, :uv:cve:`2025-38588`, :uv:cve:`2025-38601`,
    :uv:cve:`2025-38602`, :uv:cve:`2025-38604`, :uv:cve:`2025-38608`,
    :uv:cve:`2025-38609`, :uv:cve:`2025-38610`, :uv:cve:`2025-38612`,
    :uv:cve:`2025-38614`, :uv:cve:`2025-38617`, :uv:cve:`2025-38618`,
    :uv:cve:`2025-38622`, :uv:cve:`2025-38623`, :uv:cve:`2025-38624`,
    :uv:cve:`2025-38630`, :uv:cve:`2025-38634`, :uv:cve:`2025-38635`,
    :uv:cve:`2025-38639`, :uv:cve:`2025-38644`, :uv:cve:`2025-38645`,
    :uv:cve:`2025-38650`, :uv:cve:`2025-38652`, :uv:cve:`2025-38653`,
    :uv:cve:`2025-38663`, :uv:cve:`2025-38664`, :uv:cve:`2025-38665`,
    :uv:cve:`2025-38666`, :uv:cve:`2025-38668`, :uv:cve:`2025-38670`,
    :uv:cve:`2025-38671`, :uv:cve:`2025-38676`, :uv:cve:`2025-38677`,
    :uv:cve:`2025-38679`, :uv:cve:`2025-38680`, :uv:cve:`2025-38681`,
    :uv:cve:`2025-38683`, :uv:cve:`2025-38684`, :uv:cve:`2025-38685`,
    :uv:cve:`2025-38687`, :uv:cve:`2025-38691`, :uv:cve:`2025-38693`,
    :uv:cve:`2025-38694`, :uv:cve:`2025-38695`, :uv:cve:`2025-38696`,
    :uv:cve:`2025-38697`, :uv:cve:`2025-38698`, :uv:cve:`2025-38699`,
    :uv:cve:`2025-38700`, :uv:cve:`2025-38701`, :uv:cve:`2025-38702`,
    :uv:cve:`2025-38706`, :uv:cve:`2025-38707`, :uv:cve:`2025-38708`,
    :uv:cve:`2025-38711`, :uv:cve:`2025-38712`, :uv:cve:`2025-38713`,
    :uv:cve:`2025-38714`, :uv:cve:`2025-38715`, :uv:cve:`2025-38721`,
    :uv:cve:`2025-38723`, :uv:cve:`2025-38724`, :uv:cve:`2025-38725`,
    :uv:cve:`2025-38727`, :uv:cve:`2025-38728`, :uv:cve:`2025-38729`,
    :uv:cve:`2025-38732`, :uv:cve:`2025-38735`, :uv:cve:`2025-38736`,
    :uv:cve:`2025-39673`, :uv:cve:`2025-39675`, :uv:cve:`2025-39676`,
    :uv:cve:`2025-39681`, :uv:cve:`2025-39682`, :uv:cve:`2025-39683`,
    :uv:cve:`2025-39684`, :uv:cve:`2025-39685`, :uv:cve:`2025-39686`,
    :uv:cve:`2025-39687`, :uv:cve:`2025-39689`, :uv:cve:`2025-39691`,
    :uv:cve:`2025-39692`, :uv:cve:`2025-39693`, :uv:cve:`2025-39694`,
    :uv:cve:`2025-39697`, :uv:cve:`2025-39701`, :uv:cve:`2025-39702`,
    :uv:cve:`2025-39703`, :uv:cve:`2025-39706`, :uv:cve:`2025-39709`,
    :uv:cve:`2025-39710`, :uv:cve:`2025-39713`, :uv:cve:`2025-39714`,
    :uv:cve:`2025-39715`, :uv:cve:`2025-39716`, :uv:cve:`2025-39718`,
    :uv:cve:`2025-39719`, :uv:cve:`2025-39724`, :uv:cve:`2025-39730`,
    :uv:cve:`2025-39731`, :uv:cve:`2025-39734`, :uv:cve:`2025-39736`,
    :uv:cve:`2025-39737`, :uv:cve:`2025-39738`, :uv:cve:`2025-39742`,
    :uv:cve:`2025-39743`, :uv:cve:`2025-39749`, :uv:cve:`2025-39752`,
    :uv:cve:`2025-39756`, :uv:cve:`2025-39757`, :uv:cve:`2025-39759`,
    :uv:cve:`2025-39760`, :uv:cve:`2025-39766`, :uv:cve:`2025-39770`,
    :uv:cve:`2025-39772`, :uv:cve:`2025-39773`, :uv:cve:`2025-39776`,
    :uv:cve:`2025-39782`, :uv:cve:`2025-39783`, :uv:cve:`2025-39787`,
    :uv:cve:`2025-39788`, :uv:cve:`2025-39790`, :uv:cve:`2025-39794`,
    :uv:cve:`2025-39795`, :uv:cve:`2025-39798`, :uv:cve:`2025-39800`,
    :uv:cve:`2025-39801`, :uv:cve:`2025-39806`, :uv:cve:`2025-39808`,
    :uv:cve:`2025-39812`, :uv:cve:`2025-39813`, :uv:cve:`2025-39817`,
    :uv:cve:`2025-39819`, :uv:cve:`2025-39823`, :uv:cve:`2025-39824`,
    :uv:cve:`2025-39825`, :uv:cve:`2025-39826`, :uv:cve:`2025-39827`,
    :uv:cve:`2025-39828`, :uv:cve:`2025-39835`, :uv:cve:`2025-39838`,
    :uv:cve:`2025-39839`, :uv:cve:`2025-39841`, :uv:cve:`2025-39842`,
    :uv:cve:`2025-39843`, :uv:cve:`2025-39844`, :uv:cve:`2025-39845`,
    :uv:cve:`2025-39846`, :uv:cve:`2025-39847`, :uv:cve:`2025-39848`,
    :uv:cve:`2025-39849`, :uv:cve:`2025-39853`, :uv:cve:`2025-39857`,
    :uv:cve:`2025-39860`, :uv:cve:`2025-39864`, :uv:cve:`2025-39865`,
    :uv:cve:`2025-39866`, :uv:cve:`2025-39869`, :uv:cve:`2025-39870`,
    :uv:cve:`2025-39873`, :uv:cve:`2025-39876`, :uv:cve:`2025-39877`,
    :uv:cve:`2025-39880`, :uv:cve:`2025-39881`, :uv:cve:`2025-39883`,
    :uv:cve:`2025-39885`, :uv:cve:`2025-39891`, :uv:cve:`2025-39894`,
    :uv:cve:`2025-39902`, :uv:cve:`2025-39907`, :uv:cve:`2025-39909`,
    :uv:cve:`2025-39911`, :uv:cve:`2025-39913`, :uv:cve:`2025-39914`,
    :uv:cve:`2025-39916`, :uv:cve:`2025-39920`, :uv:cve:`2025-39923`,
    :uv:cve:`2025-39993`, :uv:cve:`2025-39994`, :uv:cve:`2025-39995`,
    :uv:cve:`2025-39996`, :uv:cve:`2025-39998`, :uv:cve:`2025-40001`,
    :uv:cve:`2025-40084`, :uv:cve:`2025-40085`, :uv:cve:`2025-40087`,
    :uv:cve:`2025-40088`, :uv:cve:`2025-40092`, :uv:cve:`2025-40093`,
    :uv:cve:`2025-40094`, :uv:cve:`2025-40095`, :uv:cve:`2025-40096`,
    :uv:cve:`2025-40099`, :uv:cve:`2025-40100`, :uv:cve:`2025-40103`,
    :uv:cve:`2025-40104`, :uv:cve:`2025-40105`, :uv:cve:`2025-40106`,
    :uv:cve:`2025-40300`) (:uv:bug:`58621`, :uv:bug:`58667`,
    :uv:bug:`58811`)

  * :program:`linux-signed-amd64` (:uv:cve:`2024-36331`,
    :uv:cve:`2024-47704`, :uv:cve:`2024-57924`, :uv:cve:`2024-58240`,
    :uv:cve:`2025-21861`, :uv:cve:`2025-23143`, :uv:cve:`2025-23160`,
    :uv:cve:`2025-37925`, :uv:cve:`2025-37931`, :uv:cve:`2025-37968`,
    :uv:cve:`2025-38322`, :uv:cve:`2025-38335`, :uv:cve:`2025-38347`,
    :uv:cve:`2025-38491`, :uv:cve:`2025-38500`, :uv:cve:`2025-38501`,
    :uv:cve:`2025-38502`, :uv:cve:`2025-38552`, :uv:cve:`2025-38614`,
    :uv:cve:`2025-38676`, :uv:cve:`2025-38677`, :uv:cve:`2025-39993`,
    :uv:cve:`2025-39994`, :uv:cve:`2025-39995`, :uv:cve:`2025-39996`,
    :uv:cve:`2025-39998`, :uv:cve:`2025-40001`, :uv:cve:`2025-40084`,
    :uv:cve:`2025-40085`, :uv:cve:`2025-40087`, :uv:cve:`2025-40088`,
    :uv:cve:`2025-40092`, :uv:cve:`2025-40093`, :uv:cve:`2025-40094`,
    :uv:cve:`2025-40095`, :uv:cve:`2025-40096`, :uv:cve:`2025-40099`,
    :uv:cve:`2025-40100`, :uv:cve:`2025-40103`, :uv:cve:`2025-40104`,
    :uv:cve:`2025-40105`, :uv:cve:`2025-40106`, :uv:cve:`2025-40300`)
    (:uv:bug:`58621`, :uv:bug:`58667`, :uv:bug:`58811`)

  * :program:`mariadb` (:uv:cve:`2023-52969`, :uv:cve:`2023-52970`,
    :uv:cve:`2023-52971`, :uv:cve:`2024-21096`, :uv:cve:`2025-21490`,
    :uv:cve:`2025-30693`, :uv:cve:`2025-30722`) (:uv:bug:`58617`)

  * :program:`openjdk-17` (:uv:cve:`2025-53057`, :uv:cve:`2025-53066`)
    (:uv:bug:`58741`)

  * :program:`openjpeg2` (:uv:cve:`2025-50952`) (:uv:bug:`58600`)

  * :program:`openssh` (:uv:cve:`2025-32728`) (:uv:bug:`58624`)

  * :program:`openssl` (:uv:cve:`2024-13176`, :uv:cve:`2025-9230`,
    :uv:cve:`2025-9232`) (:uv:bug:`58599`, :uv:bug:`58688`)

  * :program:`perl` (:uv:cve:`2023-31484`, :uv:cve:`2024-56406`,
    :uv:cve:`2025-40909`) (:uv:bug:`58607`)

  * :program:`postgresql-15` (:uv:cve:`2012-0868`,
    :uv:cve:`2017-7484`, :uv:cve:`2025-1094`, :uv:cve:`2025-4207`,
    :uv:cve:`2025-8713`, :uv:cve:`2025-8714`, :uv:cve:`2025-8715`)
    (:uv:bug:`58619`)

  * :program:`python-zipp` (:uv:cve:`2024-5569`) (:uv:bug:`58609`)

  * :program:`rubygems` (:uv:cve:`2023-28755`, :uv:cve:`2025-27221`)
    (:uv:bug:`58605`)

  * :program:`samba` (:uv:cve:`2025-10230`, :uv:cve:`2025-9640`)
    (:uv:bug:`58708`)

  * :program:`setuptools` (:uv:cve:`2025-47273`) (:uv:bug:`58616`)

  * :program:`sqlite3` (:uv:cve:`2025-6965`) (:uv:bug:`58610`)

  * :program:`squid` (:uv:cve:`2025-62168`) (:uv:bug:`58762`)

  * :program:`systemd` (:uv:cve:`2025-4598`) (:uv:bug:`58603`)

  * :program:`tiff` (:uv:cve:`2025-9900`) (:uv:bug:`58711`)

  * :program:`wpa` (:uv:cve:`2022-37660`) (:uv:bug:`58602`)

  * :program:`xorg-server` (:uv:cve:`2025-62229`,
    :uv:cve:`2025-62230`, :uv:cve:`2025-62231`) (:uv:bug:`58773`)


.. _debian:

* |UCSUCS| |release| includes the following updated packages from Debian 12:

  :program:`docker.io`
  :program:`aom`
  :program:`b43-fwcutter`
  :program:`base-files`
  :program:`bash`
  :program:`busybox`
  :program:`ca-certificates`
  :program:`criu`
  :program:`distro-info-data`
  :program:`e2fsprogs`
  :program:`galera-4`
  :program:`gnupg2`
  :program:`init-system-helpers`
  :program:`kexec-tools`
  :program:`libbpf`
  :program:`libtheora`
  :program:`libxslt`
  :program:`lintian`
  :program:`multipath-tools`
  :program:`postgresql-common`
  :program:`qemu`
  :program:`tini`
  :program:`tzdata`
  :program:`usb.ids`
  :program:`wireless-regdb`
  :program:`ark`
  :program:`balboa`
  :program:`botan`
  :program:`catatonit`
  :program:`cdebootstrap`
  :program:`chkrootkit`
  :program:`chromium`
  :program:`cjson`
  :program:`commons-beanutils`
  :program:`commons-vfs`
  :program:`corosync`
  :program:`dar`
  :program:`debian-edu-config`
  :program:`debian-installer`
  :program:`debian-installer-netboot-images`
  :program:`debian-security-support`
  :program:`dpdk`
  :program:`dropbear`
  :program:`erlang`
  :program:`evolution`
  :program:`firebird3.0`
  :program:`fort-validator`
  :program:`gegl`
  :program:`gimp`
  :program:`golang-github-gin-contrib-cors`
  :program:`gst-plugins-base1.0`
  :program:`gst-plugins-good1.0`
  :program:`haproxy`
  :program:`insighttoolkit4`
  :program:`insighttoolkit5`
  :program:`iperf3`
  :program:`jetty9`
  :program:`jq`
  :program:`keystone`
  :program:`kmail-account-wizard`
  :program:`krita`
  :program:`kubernetes`
  :program:`libcgi-simple-perl`
  :program:`libfile-tail-perl`
  :program:`libphp-adodb`
  :program:`libraw`
  :program:`libreoffice`
  :program:`libsoup3`
  :program:`libtpms`
  :program:`llvm-toolchain-19`
  :program:`luajit`
  :program:`lxc`
  :program:`lxd`
  :program:`mailgraph`
  :program:`mkchromecast`
  :program:`mlt`
  :program:`mono`
  :program:`mosquitto`
  :program:`nextcloud-desktop`
  :program:`nginx`
  :program:`nncp`
  :program:`node-addon-api`
  :program:`node-csstype`
  :program:`node-form-data`
  :program:`node-minipass`
  :program:`node-nodeunit`
  :program:`node-sha.js`
  :program:`node-tar-fs`
  :program:`node-tmp`
  :program:`nvda2speechd`
  :program:`pdfminer`
  :program:`prody`
  :program:`python-flask-cors`
  :program:`python-internetarchive`
  :program:`python-mitogen`
  :program:`raptor2`
  :program:`rar`
  :program:`redis`
  :program:`request-tracker4`
  :program:`request-tracker5`
  :program:`ruby-rack`
  :program:`rust-cbindgen-web`
  :program:`rustc-web`
  :program:`sash`
  :program:`shaarli`
  :program:`shibboleth-sp`
  :program:`simplesamlphp`
  :program:`snapd`
  :program:`strongswan`
  :program:`supermin`
  :program:`swift`
  :program:`thunderbird`
  :program:`tripwire`
  :program:`tryton-sao`
  :program:`tryton-server`
  :program:`tsocks`
  :program:`waitress`
  :program:`webkit2gtk`
  :program:`webpy`
  :program:`wolfssl`
  :program:`xfce4-weather-plugin`
  :program:`xrdp`
  :program:`ydotool`
  :program:`zsh`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

  :program:`python-logfmter` (:uv:bug:`58647`)

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

* The function `univention_config_is_true` has been added (:uv:bug:`58644`).

.. _changelog-domain:

***************
Domain services
***************

* Events for recyclebin restoration have been added to the admin diary
  (:uv:bug:`52202`).

.. _changelog-domain-openldap:

OpenLDAP
========

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* Structured Logging can now be activated via the UCR Variable `notifier/debug
  /structured-logging`. The UCR variable `notifier/debug/level` now allows the
  value 5 for enabling logging of TRACE log messages (:uv:bug:`58644`).

* Structured Logging can now be activated via the UCR Variable `listener/debug
  /structured-logging`. The UCR variable `listener/debug/level` now allows the
  value 5 for enabling logging of TRACE log messages (:uv:bug:`58644`).

.. _changelog-udm:

LDAP Directory Manager
======================

* A recyclebin for users and groups has been introduced (:uv:bug:`52202`).

* Added a new endpoint where LDAP attributes can be unmapped to a full UDM
  object (if the module can be identified, :uv:bug:`58792`).

* The argument `--bindpwd` has been deprecated in UDM commandline, it should be
  replaced with `--bindpwdfile` (:uv:bug:`20610`).

* All logmessages of Univention Directory Manager REST API are now in a
  structured format, if enabled via the UCR variable
  `directory/manager/rest/debug/structured-logging`. The UCR variable
  `directory/manager/rest/debug/level` now allows the value 5 for enabling
  logging of TRACE log messages. The log messages and severity has been
  overworked. Additional information like IP address, hostname, LDAP
  Distinguished Name of the requester have been added to the log information
  (:uv:bug:`58627`).

* Debug messages from Tornado are now in structured log format as well. The
  duplicated access log messages for the gateway process have been removed
  (:uv:bug:`57568`).

* Added internal cache to increase performance on searches (:uv:bug:`58697`).

* The duration of authorization operations is now logged at TRACE level
  (:uv:bug:`58756`).

* The performance of searches with delegative administration enabled has been
  improved (:uv:bug:`58789`).

* All logmessages of Univention Directory Manager are now in a structured
  format, if that is enabled in the services. The UCR variable
  `directory/manager/cmd/debug/level` now allows the value 5 for enabling
  logging of TRACE log messages. The log messages and severity has been
  overworked. Additional information like UDM object type and LDAP
  Distinguished Name has been added to the log information (:uv:bug:`58627`).

* Minor updates to the UDM policy format for delegative administration
  (:uv:bug:`58649`).

* The argument `--bindpwd` has been deprecated in UDM commandline, it should be
  replaced with `--bindpwdfile` (:uv:bug:`20610`).

* New UDM type `users/federated_account` for representing ferderated accounts
  when logging in via trusted upstream Identity Provider with UMC OIDC
  (:uv:bug:`58652`).

* A recyclebin for users and groups has been introduced (:uv:bug:`52202`).

* Changing the value of an attribute which is unique, didn't release according
  lock objects for the old attribute value, which resulted in that new objects
  using the old value couldn't be created anymore for the next 5 minutes
  (:uv:bug:`58828`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* A recyclebin for users and groups has been introduced (:uv:bug:`52202`).

* Allow adding a notification directly into the notification bar, not showing
  it as a preview in UMC (:uv:bug:`58817`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* A short notification is shown for the Univention Summit 2026 when you open
  the UMC for the first time. After that, it is discreetly sitting behind the
  bell icon (:uv:bug:`58817`).

* Fixes an issue where the UMC server does not respect the configured timeouts
  for HTTP requests, which can lead to delays in operations that involve
  communication with external services. It led particularly to failures on
  concurrent OpenID Connect (OIDC) authentication (:uv:bug:`58269`).

* The logmessages of Univention Management Console have been adapted to be
  compatible with structured logging. Structured logging can be enabled via the
  UCR variable `umc/server/debug/structured-logging`, which will become the
  default in UCS 5.2-4. The UCR variables `umc/server/debug/level` and
  `umc/module/debug/level` now allow the value 5 for enabling logging of TRACE
  log messages. The log messages and severity has been overworked. Additional
  information like request ID, IP address or LDAP DN of requester have been
  added to the log information (:uv:bug:`58627`).

* The `session-info` endpoint for the UMC now also returns the DN of the
  authenticated user (:uv:bug:`58743`).

* UMC OIDC now supports the log in with an account from an external Identiy
  Provider in Keycloak. These "federated accounts" must provide additional
  information, like a UUID and guardian role strings, to be accepted and useful
  in UMC. As UDM authorization for these accounts is based on the roles, this
  feature requires the UDM delegative administration (:uv:bug:`58652`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

* The Univention App Center update process can now be configured for
  restrictive HTTP proxy environments. The UCR variable `appcenter/update/skip-
  zsync` allows skipping zsync and downloading metadata directly via HTTPS. The
  UCR variable `appcenter/update/zsync-timeout` defines a timeout for zsync
  operations before falling back to direct download (:uv:bug:`52308`).

* Apps can now set `ListenerUDMVersion=3`. This changes the way the App Center
  creates JSON files for their Listener integration. It no longer uses the
  object's `entryUUID`, but the `UniventionObjectIdentifier` (:uv:bug:`58648`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

* The argument `--bindpwd` has been deprecated in UDM commandline, it should be
  replaced with `--bindpwdfile`. The internals of this package have been
  adapted accordingly (:uv:bug:`20610`).

.. _changelog-umc-join:

Domain join module
==================

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

.. _changelog-umc-user:

User management
===============

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Fix the UMC module's CSS to be specific and to not affect the appearance of
  the whole of UMC (:uv:bug:`58553`).

* New diagnostic modules `20_check_share_references` and `20_check_srv_records`
  as well as `24_portal_entries` have been added. The UCR variable
  `diagnostic/check/24_portal_entries/ignore` can be used to specify entry
  names that don't conform to the check criteria. The module
  `20_check_nameservers` now contains improved warning messages and a fix for a
  traceback (:uv:bug:`58634`).

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* A recyclebin for users and groups has been introduced (:uv:bug:`52202`).

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58627`).

* Performance improvements during users searches (:uv:bug:`58697`).

* Use session roles for UDM delegative administration for UMC OIDC login with
  federated account (:uv:bug:`58652`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* Adjustments for `python-logfmter` v0.0.11 have been done (:uv:bug:`58754`).

* A method to log the duration of certain operations has been added
  (:uv:bug:`58756`).

* The logformat of `univention.debug` has been made configurable to allow a
  structured format with ISO8601 dates. The old german date format is going to
  be removed in future releases. A new loglevel `TRACE` (equals the value 5)
  has been added to `univention.debug`. The library `univention.logging` now
  allows to setup structured logging using the `logfmt` format by configuring a
  `univention.debug` logging handler for the Python stdandard library logging
  system (:uv:bug:`58627`).

* New LDAP schema, ACL's for federated account object type and new UCR
  variables `ldap/authz-regexp/users` (default `true`) and `ldap/authz-regexp
  /federated-accounts` (default `false`) for the configuration of the LDAP
  servers DN mapping for federated accounts (:uv:bug:`58652`).

* A recyclebin for users and groups has been introduced (:uv:bug:`52202`).

* `univention-backup2master` now provides two hook points that allow custom
  scripts to be executed before and after the conversion from a Backup
  Directory Node to a Primary Directory Node (:uv:bug:`58778`).

* The duration of LDAP operations is now logged at TRACE level
  (:uv:bug:`58756`).

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58627`).

* The logformat of `univention.debug` has been made configurable to allow a
  structured format with ISO8601 dates. The old german date format is going to
  be removed in future releases. A new loglevel `TRACE` (equals the value 5)
  has been added to `univention.debug` (:uv:bug:`58627`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* Logging has been adapted to be compatible with structured logging. The UCR
  variable `update/debug/level` now allows the value 5 for enabling logging of
  TRACE log messages (:uv:bug:`58644`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* Add ``--import-users`` flag to ``univention-keycloak init`` (:uv:bug:`58698`).

* A new operation has been added to univention-keycloak script, this operation
  allows the creation of client scopes, and assign mappers to the scope
  (:uv:bug:`58422`).

* Added support for enabling standard token exchange on OIDC clients
  (:uv:bug:`58586`).

* Fixed a regression that breaks univention-keycloak script on kubernetes
  deployments (:uv:bug:`58588`).

.. _changelog-service-mail:

Mail services
=============

.. _changelog-service-imap:

IMAP services
-------------

* During login, it could happen that additional mail directories in dovecot
  containing only the username were created. This made it appear to the user as
  though their mail folders were emptied. The PAM login configuration for
  dovecot has been adjusted to circumvent this behaviour (:uv:bug:`57976`).

.. _changelog-service-postfix:

Postfix
-------

* During login, it could happen that additional mail directories in dovecot
  containing only the username were created. This made it appear to the user as
  though their mail folders were emptied. The PAM login configuration for
  dovecot has been adjusted to circumvent this behaviour (:uv:bug:`57976`).

.. _changelog-service-nagios:

Nagios
======

* This update enhances the alert `check_univention_mdb_maxsize` by ignoring the
  (possibly) fragmented freelist pages in the calculation of available pages
  (:uv:bug:`58668`).

* This update enhances the check `check_univention_slapd_mdb_maxsize` by
  ignoring the (possibly) fragmented freelist pages in the calculation of
  available pages (:uv:bug:`58668`).

.. _changelog-service-radius:

RADIUS
======

* The EAP module configuration setting `tls_min_version` can now be adjusted
  using the new UCR variable `freeradius/conf/tls-min-version`
  (:uv:bug:`58373`).

* The EAP module configuration setting `cipher_list` can now be adjusted using
  the new UCR variable `freeradius/conf/cipher-list`. The format is documented
  in `man openssl-ciphers` (:uv:bug:`58374`).

.. _changelog-service-pam:

PAM / Local group cache
=======================

* The SSSD Service has been configured to allow logins using the
  mailPrimaryAddress of a user during PAM login (:uv:bug:`57976`).

.. _changelog-service-network:

Networking services
===================

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-takeover:

Univention AD Takeover
======================

* Logging has been adapted to be compatible with structured logging
  (:uv:bug:`58644`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* Structured Logging can now be activated via the UCR Variable `connector/debug
  /structured-logging`. The UCR variables `connector/debug/level` and
  `connector/debug/udm/level` now allow the value 5 for enabling logging of
  TRACE log messages (:uv:bug:`58644`).

* The behavior of account locked status synchronization has been unified
  between S4-Connector and AD-Connector (:uv:bug:`58680`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* Changing the `sAMAccountName` of a user in AD led to a Python traceback in
  the AD-Connector because the post modify functions would still use the re-
  rename DN. This could also cause additional issues when later changing the
  `CN` of the object. This update fixes these issues (:uv:bug:`58738`).

* The AD-Connector now synchronizes the account lockout state from AD to UCS.
  Account unlocking is also synchronized from UCS to AD (:uv:bug:`58680`).

* An error where the DN of a synced object multiple times leading to a DN with
  mixed base was created leading to rejects was fixed (:uv:bug:`58556`).

* Logging in the UMC module has been adapted to be compatible with structured
  logging. The UCR variable `connector.*/debug/level` now allows the value 5
  for enabling logging of TRACE log messages (:uv:bug:`58644`).


.. _changelog-univention-net-install:

Univention PXE installation
======================================

* The UCS PXE Installation services provided by the package :program:`univention-net-installer` were deprecated
  and need to be removed before upgrading to UCS 5.2-4.

.. _changelog-other:

*************
Other changes
*************

* Minor updates to the UDM policy format for delegative administration
  (:uv:bug:`58649`).

* Update `python-logfmter` to v0.0.11 (:uv:bug:`58754`).


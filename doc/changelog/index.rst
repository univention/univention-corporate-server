.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
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

* |UCSUCS| |release| includes all security updates issued for |UCS| 5.2-1:

  * :program:`abseil` (:uv:cve:`2025-0838`) (:uv:bug:`58295`)

  * :program:`curl` (:uv:cve:`2024-11053`, :uv:cve:`2024-9681`,
    :uv:cve:`2025-0167`) (:uv:bug:`58098`)

  * :program:`exim4` (:uv:cve:`2025-30232`) (:uv:bug:`58157`)

  * :program:`firefox-esr` (:uv:cve:`2024-43097`, :uv:cve:`2025-1931`,
    :uv:cve:`2025-1932`, :uv:cve:`2025-1933`, :uv:cve:`2025-1934`,
    :uv:cve:`2025-1935`, :uv:cve:`2025-1936`, :uv:cve:`2025-1937`,
    :uv:cve:`2025-1938`, :uv:cve:`2025-3028`, :uv:cve:`2025-3029`,
    :uv:cve:`2025-3030`, :uv:cve:`2025-4083`, :uv:cve:`2025-4087`,
    :uv:cve:`2025-4091`, :uv:cve:`2025-4093`, :uv:cve:`2025-4920`,
    :uv:cve:`2025-4921`) (:uv:bug:`58167`, :uv:bug:`58241`,
    :uv:bug:`58289`)

  * :program:`freetype` (:uv:cve:`2025-27363`) (:uv:bug:`58105`)

  * :program:`gcc-12` (:uv:cve:`2023-4039`) (:uv:bug:`58315`)

  * :program:`ghostscript` (:uv:cve:`2025-27830`,
    :uv:cve:`2025-27831`, :uv:cve:`2025-27832`, :uv:cve:`2025-27833`,
    :uv:cve:`2025-27834`, :uv:cve:`2025-27835`, :uv:cve:`2025-27836`)
    (:uv:bug:`58148`)

  * :program:`glib2.0` (:uv:cve:`2025-3360`) (:uv:bug:`58292`)

  * :program:`glibc` (:uv:cve:`2025-0395`) (:uv:bug:`58112`)

  * :program:`imagemagick` (:uv:cve:`2025-43965`) (:uv:bug:`58283`)

  * :program:`intel-microcode` (:uv:cve:`2023-34440`,
    :uv:cve:`2023-43758`, :uv:cve:`2024-24582`, :uv:cve:`2024-28047`,
    :uv:cve:`2024-28127`, :uv:cve:`2024-28956`, :uv:cve:`2024-29214`,
    :uv:cve:`2024-31068`, :uv:cve:`2024-31157`, :uv:cve:`2024-36293`,
    :uv:cve:`2024-37020`, :uv:cve:`2024-39279`, :uv:cve:`2024-39355`,
    :uv:cve:`2024-43420`, :uv:cve:`2024-45332`, :uv:cve:`2025-20012`,
    :uv:cve:`2025-20054`, :uv:cve:`2025-20103`, :uv:cve:`2025-20623`,
    :uv:cve:`2025-24495`) (:uv:bug:`58108`, :uv:bug:`58323`)

  * :program:`jinja2` (:uv:cve:`2024-56201`, :uv:cve:`2024-56326`)
    (:uv:bug:`58099`)

  * :program:`krb5` (:uv:cve:`2024-26462`, :uv:cve:`2025-24528`)
    (:uv:bug:`58281`)

  * :program:`libcap2` (:uv:cve:`2025-1390`) (:uv:bug:`58296`)

  * :program:`libxslt` (:uv:cve:`2024-55549`, :uv:cve:`2025-24855`)
    (:uv:bug:`58110`)

  * :program:`linux` (:uv:cve:`2023-52857`, :uv:cve:`2024-24855`,
    :uv:cve:`2024-26596`, :uv:cve:`2024-26656`, :uv:cve:`2024-26767`,
    :uv:cve:`2024-26982`, :uv:cve:`2024-27056`, :uv:cve:`2024-35866`,
    :uv:cve:`2024-36908`, :uv:cve:`2024-38611`, :uv:cve:`2024-40945`,
    :uv:cve:`2024-40973`, :uv:cve:`2024-42069`, :uv:cve:`2024-42122`,
    :uv:cve:`2024-43831`, :uv:cve:`2024-45001`, :uv:cve:`2024-46733`,
    :uv:cve:`2024-46742`, :uv:cve:`2024-46753`, :uv:cve:`2024-46772`,
    :uv:cve:`2024-46774`, :uv:cve:`2024-46816`, :uv:cve:`2024-46823`,
    :uv:cve:`2024-47726`, :uv:cve:`2024-47753`, :uv:cve:`2024-47754`,
    :uv:cve:`2024-49989`, :uv:cve:`2024-50056`, :uv:cve:`2024-50061`,
    :uv:cve:`2024-50063`, :uv:cve:`2024-50246`, :uv:cve:`2024-53166`,
    :uv:cve:`2024-54458`, :uv:cve:`2024-56549`, :uv:cve:`2024-57834`,
    :uv:cve:`2024-57973`, :uv:cve:`2024-57977`, :uv:cve:`2024-57978`,
    :uv:cve:`2024-57979`, :uv:cve:`2024-57980`, :uv:cve:`2024-57981`,
    :uv:cve:`2024-57986`, :uv:cve:`2024-57993`, :uv:cve:`2024-57996`,
    :uv:cve:`2024-57997`, :uv:cve:`2024-57998`, :uv:cve:`2024-58001`,
    :uv:cve:`2024-58002`, :uv:cve:`2024-58007`, :uv:cve:`2024-58009`,
    :uv:cve:`2024-58010`, :uv:cve:`2024-58011`, :uv:cve:`2024-58013`,
    :uv:cve:`2024-58014`, :uv:cve:`2024-58016`, :uv:cve:`2024-58017`,
    :uv:cve:`2024-58020`, :uv:cve:`2024-58034`, :uv:cve:`2024-58051`,
    :uv:cve:`2024-58052`, :uv:cve:`2024-58054`, :uv:cve:`2024-58055`,
    :uv:cve:`2024-58056`, :uv:cve:`2024-58058`, :uv:cve:`2024-58061`,
    :uv:cve:`2024-58063`, :uv:cve:`2024-58068`, :uv:cve:`2024-58069`,
    :uv:cve:`2024-58071`, :uv:cve:`2024-58072`, :uv:cve:`2024-58076`,
    :uv:cve:`2024-58077`, :uv:cve:`2024-58079`, :uv:cve:`2024-58080`,
    :uv:cve:`2024-58083`, :uv:cve:`2024-58085`, :uv:cve:`2024-58086`,
    :uv:cve:`2025-21684`, :uv:cve:`2025-21700`, :uv:cve:`2025-21701`,
    :uv:cve:`2025-21702`, :uv:cve:`2025-21703`, :uv:cve:`2025-21704`,
    :uv:cve:`2025-21705`, :uv:cve:`2025-21706`, :uv:cve:`2025-21707`,
    :uv:cve:`2025-21708`, :uv:cve:`2025-21711`, :uv:cve:`2025-21715`,
    :uv:cve:`2025-21716`, :uv:cve:`2025-21718`, :uv:cve:`2025-21719`,
    :uv:cve:`2025-21722`, :uv:cve:`2025-21724`, :uv:cve:`2025-21725`,
    :uv:cve:`2025-21726`, :uv:cve:`2025-21727`, :uv:cve:`2025-21728`,
    :uv:cve:`2025-21731`, :uv:cve:`2025-21734`, :uv:cve:`2025-21735`,
    :uv:cve:`2025-21736`, :uv:cve:`2025-21738`, :uv:cve:`2025-21744`,
    :uv:cve:`2025-21745`, :uv:cve:`2025-21748`, :uv:cve:`2025-21749`,
    :uv:cve:`2025-21750`, :uv:cve:`2025-21753`, :uv:cve:`2025-21756`,
    :uv:cve:`2025-21758`, :uv:cve:`2025-21760`, :uv:cve:`2025-21761`,
    :uv:cve:`2025-21762`, :uv:cve:`2025-21763`, :uv:cve:`2025-21764`,
    :uv:cve:`2025-21765`, :uv:cve:`2025-21766`, :uv:cve:`2025-21767`,
    :uv:cve:`2025-21772`, :uv:cve:`2025-21775`, :uv:cve:`2025-21776`,
    :uv:cve:`2025-21779`, :uv:cve:`2025-21780`, :uv:cve:`2025-21781`,
    :uv:cve:`2025-21782`, :uv:cve:`2025-21785`, :uv:cve:`2025-21787`,
    :uv:cve:`2025-21790`, :uv:cve:`2025-21791`, :uv:cve:`2025-21792`,
    :uv:cve:`2025-21794`, :uv:cve:`2025-21795`, :uv:cve:`2025-21796`,
    :uv:cve:`2025-21799`, :uv:cve:`2025-21802`, :uv:cve:`2025-21804`,
    :uv:cve:`2025-21806`, :uv:cve:`2025-21811`, :uv:cve:`2025-21812`,
    :uv:cve:`2025-21814`, :uv:cve:`2025-21819`, :uv:cve:`2025-21820`,
    :uv:cve:`2025-21821`, :uv:cve:`2025-21823`, :uv:cve:`2025-21826`,
    :uv:cve:`2025-21829`, :uv:cve:`2025-21830`, :uv:cve:`2025-21832`,
    :uv:cve:`2025-21835`, :uv:cve:`2025-21838`, :uv:cve:`2025-21853`,
    :uv:cve:`2025-21918`, :uv:cve:`2025-22126`, :uv:cve:`2025-37838`)
    (:uv:bug:`58106`, :uv:bug:`58197`, :uv:bug:`58227`)

  * :program:`linux-signed-amd64` (:uv:cve:`2023-52857`,
    :uv:cve:`2024-24855`, :uv:cve:`2024-26656`, :uv:cve:`2024-26767`,
    :uv:cve:`2024-26982`, :uv:cve:`2024-27056`, :uv:cve:`2024-35866`,
    :uv:cve:`2024-36908`, :uv:cve:`2024-38611`, :uv:cve:`2024-40945`,
    :uv:cve:`2024-40973`, :uv:cve:`2024-42069`, :uv:cve:`2024-42122`,
    :uv:cve:`2024-43831`, :uv:cve:`2024-45001`, :uv:cve:`2024-46733`,
    :uv:cve:`2024-46742`, :uv:cve:`2024-46753`, :uv:cve:`2024-46772`,
    :uv:cve:`2024-46774`, :uv:cve:`2024-46816`, :uv:cve:`2024-46823`,
    :uv:cve:`2024-47726`, :uv:cve:`2024-47753`, :uv:cve:`2024-47754`,
    :uv:cve:`2024-49989`, :uv:cve:`2024-50056`, :uv:cve:`2024-50061`,
    :uv:cve:`2024-50063`, :uv:cve:`2024-50246`, :uv:cve:`2024-53166`,
    :uv:cve:`2024-56549`, :uv:cve:`2024-57977`, :uv:cve:`2024-58002`,
    :uv:cve:`2024-58079`, :uv:cve:`2025-21684`, :uv:cve:`2025-21700`,
    :uv:cve:`2025-21701`, :uv:cve:`2025-21702`, :uv:cve:`2025-21703`,
    :uv:cve:`2025-21704`, :uv:cve:`2025-21756`, :uv:cve:`2025-21838`,
    :uv:cve:`2025-21853`, :uv:cve:`2025-21918`, :uv:cve:`2025-22126`,
    :uv:cve:`2025-37838`) (:uv:bug:`58104`, :uv:bug:`58198`,
    :uv:bug:`58227`)

  * :program:`mariadb` (:uv:cve:`2024-21096`, :uv:cve:`2025-21490`)
    (:uv:bug:`58102`, :uv:bug:`58109`)

  * :program:`net-tools` (:uv:cve:`2025-46836`) (:uv:bug:`58293`)

  * :program:`nvidia-graphics-drivers` (:uv:cve:`2024-0131`,
    :uv:cve:`2024-0147`, :uv:cve:`2024-0149`, :uv:cve:`2024-0150`,
    :uv:cve:`2024-53869`, :uv:cve:`2025-23244`) (:uv:bug:`58290`)

  * :program:`openjdk-17` (:uv:cve:`2025-21587`, :uv:cve:`2025-30691`,
    :uv:cve:`2025-30698`) (:uv:bug:`58274`)

  * :program:`openssh` (:uv:cve:`2025-32728`) (:uv:bug:`58297`)

  * :program:`openssl` (:uv:cve:`2024-13176`) (:uv:bug:`58287`)

  * :program:`perl` (:uv:cve:`2024-56406`) (:uv:bug:`58194`)

  * :program:`poppler` (:uv:cve:`2023-34872`, :uv:cve:`2024-56378`,
    :uv:cve:`2025-32364`, :uv:cve:`2025-32365`) (:uv:bug:`58288`)

  * :program:`postgresql-15` (:uv:cve:`2025-1094`,
    :uv:cve:`2025-4207`) (:uv:bug:`58115`, :uv:bug:`58291`)

  * :program:`python-h11` (:uv:cve:`2025-43859`) (:uv:bug:`58298`)

  * :program:`python3.11` (:uv:cve:`2025-0938`, :uv:cve:`2025-1795`)
    (:uv:bug:`58286`)

  * :program:`shadow` (:uv:cve:`2023-29383`, :uv:cve:`2023-4641`)
    (:uv:bug:`58284`)

  * :program:`sssd` (:uv:cve:`2023-3758`) (:uv:bug:`58107`)

  * :program:`vim` (:uv:cve:`2023-2610`, :uv:cve:`2023-4738`,
    :uv:cve:`2023-4752`, :uv:cve:`2023-4781`, :uv:cve:`2023-5344`,
    :uv:cve:`2024-22667`, :uv:cve:`2024-43802`, :uv:cve:`2024-47814`)
    (:uv:bug:`58103`)

  * :program:`wget` (:uv:cve:`2024-38428`) (:uv:bug:`58111`)

  * :program:`xz-utils` (:uv:cve:`2025-31115`) (:uv:bug:`58168`)


.. _debian:

* |UCSUCS| |release| includes the following updated packages from Debian 12:

  :program:`docker.io`
  :program:`fig2dev`
  :program:`base-files`
  :program:`bash`
  :program:`busybox`
  :program:`containerd`
  :program:`debian-archive-keyring`
  :program:`distro-info-data`
  :program:`dns-root-data`
  :program:`initramfs-tools`
  :program:`nvidia-graphics-drivers-tesla`
  :program:`qemu`
  :program:`rsyslog`
  :program:`spamassassin`
  :program:`systemd`
  :program:`tzdata`
  :program:`wireless-regdb`
  :program:`xen`
  :program:`389-ds-base`
  :program:`atop`
  :program:`bup`
  :program:`cdebootstrap`
  :program:`chkrootkit`
  :program:`chromium`
  :program:`crowdsec`
  :program:`dacite`
  :program:`dar`
  :program:`dcmtk`
  :program:`debian-installer`
  :program:`debian-installer-netboot-images`
  :program:`debian-ports-archive-keyring`
  :program:`debian-security-support`
  :program:`dgit`
  :program:`djoser`
  :program:`dpdk`
  :program:`edk2`
  :program:`elpa`
  :program:`erlang`
  :program:`fossil`
  :program:`gensim`
  :program:`golang-github-containerd-stargz-snapshotter`
  :program:`golang-github-containers-buildah`
  :program:`golang-github-openshift-imagebuilder`
  :program:`graphicsmagick`
  :program:`haproxy`
  :program:`igtf-policy-bundle`
  :program:`iptables-netflow`
  :program:`jetty9`
  :program:`joblib`
  :program:`lemonldap-ng`
  :program:`libapache-mod-jk`
  :program:`libapache2-mod-auth-openidc`
  :program:`libbson-xs-perl`
  :program:`libdata-entropy-perl`
  :program:`libeconf`
  :program:`libpod`
  :program:`librabbitmq`
  :program:`libreoffice`
  :program:`libsub-handlesvia-perl`
  :program:`libtar`
  :program:`linuxcnc`
  :program:`logcheck`
  :program:`ltt-control`
  :program:`lttng-modules`
  :program:`mediawiki`
  :program:`mercurial`
  :program:`monero`
  :program:`mongo-c-driver`
  :program:`mozc`
  :program:`ndcube`
  :program:`network-manager`
  :program:`nginx`
  :program:`node-axios`
  :program:`node-fstream-ignore`
  :program:`node-js-sdsl`
  :program:`node-postcss`
  :program:`node-recast`
  :program:`node-redis`
  :program:`node-rollup`
  :program:`node-send`
  :program:`node-serialize-javascript`
  :program:`nvidia-graphics-drivers-tesla-535`
  :program:`nvidia-open-gpu-kernel-modules`
  :program:`nvidia-settings`
  :program:`open-vm-tools`
  :program:`openh264`
  :program:`openrazer`
  :program:`opensaml`
  :program:`opensnitch`
  :program:`openvpn`
  :program:`php-nesbot-carbon`
  :program:`php8.2`
  :program:`phpmyadmin`
  :program:`policyd-rate-limit`
  :program:`prometheus`
  :program:`prometheus-postfix-exporter`
  :program:`puma`
  :program:`python-pycdlib`
  :program:`qtbase-opensource-src`
  :program:`rails`
  :program:`rapiddisk`
  :program:`redis`
  :program:`renaissance`
  :program:`request-tracker4`
  :program:`request-tracker5`
  :program:`ruby-rack`
  :program:`runit-services`
  :program:`sash`
  :program:`seqan3`
  :program:`simgear`
  :program:`skeema`
  :program:`skopeo`
  :program:`subversion`
  :program:`sunpy`
  :program:`telegram-desktop`
  :program:`thunderbird`
  :program:`tomcat10`
  :program:`trafficserver`
  :program:`tripwire`
  :program:`twitter-bootstrap3`
  :program:`twitter-bootstrap4`
  :program:`user-mode-linux`
  :program:`vagrant`
  :program:`varnish`
  :program:`vips`
  :program:`webkit2gtk`
  :program:`xmedcon`
  :program:`zsh`

.. _maintained:

* The following packages have been moved to the maintained repository of |UCS|:

  :program:`nvidia-graphics-drivers-tesla-535`

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* Bash shell command line completion was not available by default for
  interactive non-login shells, affecting screen and ``sudo`` sessions. The UCR
  template for :file:`/etc/bash.bashrc` has been adjusted to enable command line
  completion by default for interactive shells (:uv:bug:`54717`).

* The :program:`route` tool from the package is used on some |UCS| systems for the
  configuration of additional routes through |UCSUCRVs|. Due to a change in the
  package dependencies with |UCS| 5.2-0, the :program:`net-tools` package was no longer
  installed automatically, which meant that these additional routes were no
  longer set automatically when configuring the network interfaces. The package
  dependencies have been adjusted accordingly so that this package is now
  automatically installed again (:uv:bug:`58061`).

* This update delivers the new command line tool :program:`univention-lmdb-fragmentation`
  that can be used to detect excessive fragmentation in the LMDB databases
  used in |UCS| (:uv:bug:`58047`).

.. _changelog-basis-other:

Other system services
=====================

* The allowed machine password length has been increased from 60 to 256
  characters (:uv:bug:`52575`).

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-domain-openldap:

OpenLDAP
========

* When checking for password expiry the :program:`OpenLDAP` overlay module ``shdowbind``
  looks at the LDAP attribute ``shadowMax``, which is stored at the user accounts. It
  treated a value of ``0`` specially as *"no expiry check needed"*.
  Univention improved input value validation, because a value of ``0`` was consider invalid before.
  This update changes that and it treats it as a normal value. This change
  became necessary to make the handling of password expiry more consistent on
  the day of expiry between ``pam_unix``, :program:`OpenLDAP` and :program:`Kerberos`
  (:uv:bug:`58048`).

* The tool ``slapschema`` returned an exit status of zero if the last object
  checked was OK, even if it found problems with previous objects. So it
  behaved a bit like the ``-c`` option was given. Now the tool stops on first
  error unless ``-c`` is given and returns a non-zero exit code in case a problem
  is detected on any of the objects checked (:uv:bug:`58120`).

.. _changelog-udm:

LDAP Directory Manager
======================

* First incremental release for new experimental feature delegate
  administration (:uv:bug:`58113`).

* Improved performance when removing computer objects in environments with many DNS
  host records significantly (:uv:bug:`58119`).

* Attributes containing distinguished names as values were normalized and thus
  may have differed in string representation from the distinguished names
  of LDAP objects themselves. This could lead to errors in the |UMC| not recognizing
  the correct item in ``combobox`` widgets. This has been aligned, all data is now
  written un-normalized (:uv:bug:`58261`).

* In the experimental feature *"delegative administration"*,
  administrators can now define writable attributes for |UDM| objects (:uv:bug:`58201`).

* The PAM module ``pam_unix`` interprets ``(shadowLastChange + shadowMax)`` as a
  date where the password is still valid. For example, with ``shadowMax=1` this PAM
  module considers a password valid during the day after the change. That
  causes inconsistent behavior when compared to :program:`Kerberos`, where
  ``krb5PasswordEnd`` defines a definite point in time, where the password is
  considered invalid and |UDM| sets ``krb5PasswordEnd`` to the beginning of the day of
  expiry. ``shadowMax`` is an LDAP attribute that is added to user accounts
  during password change and the value is determined by the |UDM| password
  history policy applied to the user. |UDM| now sets ``shadowMax`` to
  ``(pwhistoryPolicy.expiryInterval -1)`` to compensate for the behavior of
  ``pam_unix`` and make it more consistent with the behavior of :program:`Kerberos`
  (:uv:bug:`58048`).

* |UDM| hook extension modules could overwrite members of the global Python
  namespace, possibly leading to trivial conflicts between imported modules.
  The import of these modules has been adjusted to sandbox their global
  namespace and selectively import only the intended subclass types
  (:uv:bug:`57630`).

* The ``univentionObjectIdentifier`` |UDM| property has been added to all |UDM|
  modules. It is set to an auto-generated value if none was specified in the
  create request (:uv:bug:`58252`, :uv:bug:`58318`).

* An LDAP equality index is now created for the attribute
  ``univentionObjectIdentifier`` (:uv:bug:`57393`).

* The OpenAPI schema has been adjusted to allow the specification of multiple
  policies for UCR policies (:uv:bug:`57988`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* The *Tree* widget now correctly encodes its content, effectively removing an
  cross-site scripting (XSS) attack vector (:uv:bug:`49001`).

* A syntax check error message didn't properly escape HTML code in XSS
  attempts on UCR keys (:uv:bug:`58279`).

* Certain widgets, for example, in the *Users Module*, weren't considered as empty by
  the frontend although they were. This led to values being sent to backend
  that should have been ignored. This has been fixed (:uv:bug:`58130`).

* Improved the styling of the *MultiInput* widget when displaying more than two
  input fields to enhance UI appearance in the |UMC| (:uv:bug:`58122`).

.. _changelog-umc-portal:

Univention Portal
=================

* The *Portal* now sanitizes HTML content in tooltips and notifications
  to prevent cross-site scripting (XSS) vulnerabilities (:uv:bug:`58311`).

* The server's address is no longer included in the :file:`meta.json` file by default
  and is now only visible during system setup to prevent information disclosure (:uv:bug:`58280`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* Unused information for un-authenticate user has been removed from the :file:`meta.json` to prevent information disclosures (:uv:bug:`54257`).

* The server's address is no longer included in the :file:`meta.json` file by default
  and is now only visible during system setup to prevent information disclosure (:uv:bug:`58280`).

* Logging of failure reasons when retrieving the ``OIDC`` access token has been
  improved (:uv:bug:`58114`).

* Logging of stack traces is now done with ``ERROR`` facility and they are
  additionally logged to the log files of the modules (:uv:bug:`46057`).

* A configuration option to deactivate checks for ``TLS`` encrypted connections has
  been added the *UMC Server*
  to support using the ``SASL`` mechanism ``OAUTHBEARER`` in :program:`Kubernetes`
  environments (:uv:bug:`58210`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* Applied stricter content sanitization in the App Center to prevent
  exploitation via Cross-Site Scripting (XSS) and related attack vectors
  (:uv:bug:`58327`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* Relax hostname length limit from 13 to 15 characters (:uv:bug:`56128`).

.. _changelog-umc-join:

Domain join module
==================

* The scripts :command:`univention-join` and :command:`univention-run-join-scripts` now set the
  ``umask`` to ``0022`` so that customized more restricted settings don't cause
  problems in join scripts and listener modules (:uv:bug:`56634`).

* The usage of ``chown`` has been made future proof to prevent a misleading error
  message in the join log file (:uv:bug:`58033`).

.. _changelog-umc-user:

User management
===============

* Administrators can specify trusted hosts to bypass the |UMC| :program:`self-service` rate
  limit. This can be done by adding the hosts to the |UCSUCRV| :envvar:`umc/self-
  service/rate-limit/trusted-hosts` (:uv:bug:`58214`).

* Users can now edit their country in the self service profile view again. The
  LDAP attribute ``c`` has been added to the default list of allowed attributes
  to be changed in the profile view. Since |UCS| 5.2 the ``Country`` property
  corresponds to the LDAP attribute ``c`` instead of ``st`` (:uv:bug:`57397`).

* The :program:`Self-Service` |UMC| module now attempts to reconnect if its connection to
  the :program:`PostgreSQL` database is interrupted during fetching of password reset
  tokens. If the reconnection attempt fails, the connection is re-established
  on the next request (:uv:bug:`58159`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* This update delivers a new diagnostic module ``70_lmdb_fragmentation`` that can
  be used to detect excessive fragmentation in the LMDB databases used in |UCS|
  (:uv:bug:`58047`).

* A new script was added: ``univention-export-anonymized-ldap`` creates an
  offline copy of the LDAP server. It anonymizes the data with regards
  to user data such as names, mail addresses, and passwords. Use case is a file
  that could be used in testing environments, for example, to analyze performance
  (:uv:bug:`58247`).

.. _changelog-umc-policy:

Policies
========

* The allowed machine password length has been increased from 27 to 256
  characters (:uv:bug:`52575`).

.. _changelog-umc-ucr:

Univention Configuration Registry module
========================================

* The |UMC| module didn't properly escape HTML code forcefully injected from the
  server side in cross-site scripting (XSS) attempts on UCR keys (:uv:bug:`58279`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* The |UDM| *Grid* widget now correctly encodes its content, effectively removing
  an cross-site scripting (XSS) attack vector (:uv:bug:`49001`).

* First incremental release for new experimental feature delegate
  administration (:uv:bug:`58113`).

* In the experimental feature *"delegative administration"* one can now define
  writable attributes for |UDM| objects (:uv:bug:`58201`).

* The performance of receiving object representations in |UDM| HTTP REST API and the
  |UMC| module has been improved (:uv:bug:`58278`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* The initial objects during the LDAP bootstrapping of new installations now
  automatically set generated values for ``univenitonObjectIdentifier``
  (:uv:bug:`58310`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* The options ``startTls`` and ``connectionPooling`` are incompatible in :program:`Keycloak`
  26. As of this version, ``connectionPooling`` will only be activated if
  ``startTls`` is deactivated. This is due to underlying limitations with pooling
  secure (``TLS``) connections (:uv:bug:`58183`).

* Add ``basic`` scope as default scope when creating ``OIDC`` relying party clients
  (:uv:bug:`58254`).

.. _changelog-service-mail:

Mail services
=============

.. _changelog-service-imap:

IMAP services
-------------

* In certain scenarios the ``pwdChangeNextLogin`` enabled state of users were
  reset during ``IMAP`` authentication in the ``PAM`` stack of dovecot. This is now
  prevented (:uv:bug:`58127`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* The PAM module ``pam_unix`` interprets ``(shadowLastChange + shadowMax)`` as a
  date where the password is still valid. For example, with ``shadowMax=1` this PAM
  module considers a password valid during the day after the change. That
  causes inconsistent behavior when compared to :program:`Kerberos`, where
  ``krb5PasswordEnd`` defines a definite point in time, where the password is
  considered invalid and |UDM| sets ``krb5PasswordEnd`` to the beginning of the day of
  expiry. ``shadowMax`` is an LDAP attribute that is added to user accounts
  during password change and the value is determined by the |UDM| password
  history policy applied to the user. |UDM| now sets ``shadowMax`` to
  ``(pwhistoryPolicy.expiryInterval -1)`` to compensate for the behavior of
  ``pam_unix`` and make it more consistent with the behavior of :program:`Kerberos`
  (:uv:bug:`58048`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* The PAM module ``pam_unix`` interprets ``(shadowLastChange + shadowMax)`` as a
  date where the password is still valid. For example, with ``shadowMax=1` this PAM
  module considers a password valid during the day after the change. That
  causes inconsistent behavior when compared to :program:`Kerberos`, where
  ``krb5PasswordEnd`` defines a definite point in time, where the password is
  considered invalid and |UDM| sets ``krb5PasswordEnd`` to the beginning of the day of
  expiry. ``shadowMax`` is an LDAP attribute that is added to user accounts
  during password change and the value is determined by the |UDM| password
  history policy applied to the user. |UDM| now sets ``shadowMax`` to
  ``(pwhistoryPolicy.expiryInterval -1)`` to compensate for the behavior of
  ``pam_unix`` and make it more consistent with the behavior of :program:`Kerberos`. The
  :program:`AD-Connector` has been adjusted accordingly (:uv:bug:`58048`).

.. _changelog-other:

*************
Other changes
*************

* A configuration option to deactivate checks for ``TLS`` encrypted connections has
  been added to support using the ``SASL`` mechanism ``OAUTHBEARER`` in :program:`Kubernetes`
  environments (:uv:bug:`58210`).

* A segmentation fault is prevented if the :file:`JWKS` file for the OpenID Connect provider is
  larger than 8192 bytes (:uv:bug:`57508`).


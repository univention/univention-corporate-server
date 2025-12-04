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

* |UCSUCS| |release| includes all security updates issued for UCS 5.2-2:

  * :program:`firefox-esr` (:uv:cve:`2025-5263`, :uv:cve:`2025-5264`,
    :uv:cve:`2025-5266`, :uv:cve:`2025-5267`, :uv:cve:`2025-5268`,
    :uv:cve:`2025-5269`, :uv:cve:`2025-8027`, :uv:cve:`2025-8028`,
    :uv:cve:`2025-8029`, :uv:cve:`2025-8030`, :uv:cve:`2025-8031`,
    :uv:cve:`2025-8032`, :uv:cve:`2025-8033`, :uv:cve:`2025-8034`,
    :uv:cve:`2025-8035`, :uv:cve:`2025-9179`, :uv:cve:`2025-9180`,
    :uv:cve:`2025-9181`, :uv:cve:`2025-9185`) (:uv:bug:`58441`,
    :uv:bug:`58491`, :uv:bug:`58540`)

  * :program:`gdk-pixbuf` (:uv:cve:`2025-6199`) (:uv:bug:`58409`)

  * :program:`gnutls28` (:uv:cve:`2025-32988`, :uv:cve:`2025-32989`,
    :uv:cve:`2025-32990`, :uv:cve:`2025-6395`) (:uv:bug:`58480`)

  * :program:`icu` (:uv:cve:`2025-5222`) (:uv:bug:`58439`)

  * :program:`jpeg-xl` (:uv:cve:`2023-0645`, :uv:cve:`2023-35790`,
    :uv:cve:`2024-11403`, :uv:cve:`2024-11498`) (:uv:bug:`58452`)

  * :program:`libxml2` (:uv:cve:`2022-49043`, :uv:cve:`2023-39615`,
    :uv:cve:`2023-45322`, :uv:cve:`2024-25062`, :uv:cve:`2024-34459`,
    :uv:cve:`2024-56171`, :uv:cve:`2025-24928`, :uv:cve:`2025-27113`,
    :uv:cve:`2025-32414`, :uv:cve:`2025-32415`) (:uv:bug:`58438`)

  * :program:`libxslt` (:uv:cve:`2023-40403`, :uv:cve:`2024-55549`,
    :uv:cve:`2025-24855`, :uv:cve:`2025-7424`) (:uv:bug:`58541`)

  * :program:`linux` (:uv:cve:`2024-26739`, :uv:cve:`2024-26807`,
    :uv:cve:`2024-28956`, :uv:cve:`2024-35790`, :uv:cve:`2024-36350`,
    :uv:cve:`2024-36357`, :uv:cve:`2024-36903`, :uv:cve:`2024-36913`,
    :uv:cve:`2024-36927`, :uv:cve:`2024-38541`, :uv:cve:`2024-41013`,
    :uv:cve:`2024-43840`, :uv:cve:`2024-53203`, :uv:cve:`2024-53209`,
    :uv:cve:`2024-56758`, :uv:cve:`2024-57883`, :uv:cve:`2025-21645`,
    :uv:cve:`2025-21816`, :uv:cve:`2025-21839`, :uv:cve:`2025-21931`,
    :uv:cve:`2025-22062`, :uv:cve:`2025-22119`, :uv:cve:`2025-23144`,
    :uv:cve:`2025-27558`, :uv:cve:`2025-37797`, :uv:cve:`2025-37819`,
    :uv:cve:`2025-37958`, :uv:cve:`2025-37967`, :uv:cve:`2025-38000`,
    :uv:cve:`2025-38067`, :uv:cve:`2025-38074`, :uv:cve:`2025-38083`,
    :uv:cve:`2025-38084`, :uv:cve:`2025-38086`, :uv:cve:`2025-38088`,
    :uv:cve:`2025-38090`, :uv:cve:`2025-38215`, :uv:cve:`2025-38225`,
    :uv:cve:`2025-38230`) (:uv:bug:`58294`, :uv:bug:`58528`)

  * :program:`linux-signed-amd64` (:uv:cve:`2024-26739`,
    :uv:cve:`2024-26807`, :uv:cve:`2024-28956`, :uv:cve:`2024-35790`,
    :uv:cve:`2024-36350`, :uv:cve:`2024-36357`, :uv:cve:`2024-36903`,
    :uv:cve:`2024-36913`, :uv:cve:`2024-36927`, :uv:cve:`2024-38541`,
    :uv:cve:`2024-41013`, :uv:cve:`2024-43840`, :uv:cve:`2024-53203`,
    :uv:cve:`2024-53209`, :uv:cve:`2024-56758`, :uv:cve:`2024-57883`,
    :uv:cve:`2025-21645`, :uv:cve:`2025-21816`, :uv:cve:`2025-21839`,
    :uv:cve:`2025-21931`, :uv:cve:`2025-22062`, :uv:cve:`2025-22119`,
    :uv:cve:`2025-23144`, :uv:cve:`2025-27558`, :uv:cve:`2025-37797`,
    :uv:cve:`2025-37819`, :uv:cve:`2025-37958`, :uv:cve:`2025-37967`,
    :uv:cve:`2025-38000`, :uv:cve:`2025-38067`, :uv:cve:`2025-38074`,
    :uv:cve:`2025-38083`, :uv:cve:`2025-38084`, :uv:cve:`2025-38086`,
    :uv:cve:`2025-38088`, :uv:cve:`2025-38090`, :uv:cve:`2025-38215`,
    :uv:cve:`2025-38225`, :uv:cve:`2025-38230`) (:uv:bug:`58294`,
    :uv:bug:`58528`)

  * :program:`openjdk-17` (:uv:cve:`2025-21587`, :uv:cve:`2025-30691`,
    :uv:cve:`2025-30698`, :uv:cve:`2025-30749`, :uv:cve:`2025-30754`,
    :uv:cve:`2025-50059`, :uv:cve:`2025-5010`) (:uv:bug:`58529`)

  * :program:`rhonabwy` (:uv:cve:`2024-25714`) (:uv:bug:`58389`)

  * :program:`squid` (:uv:cve:`2023-5824`, :uv:cve:`2025-54574`)
    (:uv:bug:`58539`)

  * :program:`sudo` (:uv:cve:`2025-32462`) (:uv:bug:`58440`)

  * :program:`xorg-server` (:uv:cve:`2025-49175`,
    :uv:cve:`2025-49176`, :uv:cve:`2025-49177`, :uv:cve:`2025-49178`,
    :uv:cve:`2025-49179`, :uv:cve:`2025-49180`) (:uv:bug:`58437`)


.. _debian:

* |UCSUCS| |release| includes the following updated packages from Debian 12:

  :program:`aide`
  :program:`catdoc`
  :program:`chromium`
  :program:`djvulibre`
  :program:`ffmpeg`
  :program:`gst-plugins-bad1.0`
  :program:`konsole`
  :program:`libblockdev`
  :program:`libxml2`
  :program:`mediawiki`
  :program:`node-cipher-base`
  :program:`nodejs`
  :program:`pgpool2`
  :program:`php8.2`
  :program:`qemu`
  :program:`redis`
  :program:`ring`
  :program:`slurm-wlm`
  :program:`sope`
  :program:`thunderbird`
  :program:`trafficserver`
  :program:`udisks2`
  :program:`unbound`
  :program:`webkit2gtk`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

  :program:`asgi-correlation-id` (:uv:bug:`58421`), :program:`nats-py`
  (:uv:bug:`58420`), :program:`univention-provisioning-stack-listener`
  (:uv:bug:`58423`)

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-domain-openldap:

OpenLDAP
========

* OpenLDAP increased the maximum number of indexed attributes from 128 to 256
  (:uv:bug:`58443`).

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* During the |UCS| domain join process, :program:`slapd` fails to start
  if schema lines exceed 2000 bytes. The issue is resolved
  by wrapping long ``attributeType`` and ``objectClass`` lines at 1500 characters
  to prevent this failure (:uv:bug:`56247`).

* Fixed a race condition that could prevent listener modules from initializing
  properly (:uv:bug:`58522`).

.. _changelog-udm:

LDAP Directory Manager
======================

* The experimental delegative administration feature has been integrated into
  the |UDM| core library (:uv:bug:`58432`).

* The primary groups for users and computers are now configurable at the parent
  container objects where an object is going to be created (:uv:bug:`58356`).

* Further improvements for the delegative administration feature have been
  implemented (:uv:bug:`58517`).

* Clean up references to apps installed on a domain controller or member server
  when the computer object is removed (:uv:bug:`54892`).

* Experimental support for delegative administration has been added to the |UDM|
  REST API (:uv:bug:`58432`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-server:

Univention Management Console server
====================================

* The error message for 502/503 HTTP errors for services underneath of
  ``/univention/``, like the :program:`Guardian`, has been corrected (:uv:bug:`58404`).

* Fixed authentication failure lockout functionality for the |UMC|
  to properly track and enforce login attempt limits
  (:uv:bug:`57968`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* Fixed the directory where the *App Center* stores the cache for the next release
  during :command:`univention-app update-check` (:uv:bug:`58240`).

* The *App Center* cache is invalidated if the download fails due to network
  issues to avoid inconsistency in the *App Center* cache (:uv:bug:`58469`).

.. _changelog-umc-user:

User management
===============

* Deactivate an unnecessary :program:`systemd` service when installing the :program:`Self Service` app
  on a Replica Directory Node (:uv:bug:`51256`).

.. _changelog-umc-reports:

Univention Directory Reports
============================

* The creation of reports now evaluates the authorization rules
  (:uv:bug:`58517`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* This update ships the UMC diagnostic plugin ``71_samba_memberOf`` which
  checks that the ``memberOf`` attribute is visible in the output of
  :command:`univention-s4search` and offers possible measures in case that it ``memberOf`` attribute isn't
  visible. This update is a follow-up to :uv:kb:`18673` (:uv:bug:`53882`).

* The output of the diagnostic module ``58_univentionObjectIdentifier`` is now
  more verbose and shows the affected objects (:uv:bug:`58446`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* The experimental delegative administration feature has been integrated into
  the |UDM| core library (:uv:bug:`58432`).

* The primary groups for users and computers are now configurable at the parent
  container objects where an object is going to be created (:uv:bug:`58356`).

* The default global search container, for example *"All containers"*, can now be
  deactivated through the |UCSUCRV|
  :envvar:`directory/manager/web/modules/search/global-search`.
  If deactivated, you can enable the |UCSUCRV|
  :envvar:`directory/manager/web/modules/search/default-search`
  to limit searches to module-specific default containers. This improves search
  performance and result relevance, especially in large environments with many
  objects (:uv:bug:`58418`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* The script :command:`univention-update-univention-object-identifier` now provides a
  ``--dry-run`` option (:uv:bug:`58446`).

* :command:`ldap_setup_index` now checks if number of indexed attributes would exceed
  maximum number of :program:`lmdb` sub-databases (:uv:bug:`58443`).

* The primary groups for users and computers are now configurable at the parent
  container objects where an object is going to be created (:uv:bug:`58356`).

* The experimental delegative administration feature has been integrated into
  the |UDM| core library (:uv:bug:`58432`).

* Further improvements for the delegative administration feature have been
  implemented (:uv:bug:`58517`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* The pre-update script has been updated to run :program:`univention-prune-kernels`, in
  case the |UCSUCRV| :envvar:`update52/pruneoldkernel` is enabled, before all the
  other checks (:uv:bug:`58386`).

* The *JFrog Artifactory* with authentication return a 403 instead of 401 when
  authentication is missing.
  This isn't correct.
  To solve that problem,
  a preemptive authentication was added
  which first tries it with credentials,
  but then also proceeds if they're URL-encoded (:uv:bug:`58371`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* Add a ``--force`` flag to :command:`oidc/rp create` and :command:`saml/sp create` which updates
  existing Keycloak clients to the configuration given by the command
  (:uv:bug:`58426`).

* The command :command:`univention-keycloak saml-client-nameid-mapper create`
  wasn't idempotent and failed with a traceback
  if the mapper already existed,
  making it unsuitable for the use in join scripts.
  This has been fixed (:uv:bug:`58544`).

* Implement compatibility with Keycloak 26.3.1 authentication flows
  (:uv:bug:`58501`).

.. _changelog-service-mail:

Mail services
=============

* The Fetchmail listener module now uses :program:`systemd` instead of the
  :program:`SysV` init script ``/etc/init.d/fetchmail`` (:uv:bug:`58532`).

.. _changelog-service-radius:

RADIUS
======

* The log file :file:`/var/log/univention/radius_ntlm_auth.log` is no longer emptied
  during package updates (:uv:bug:`58425`).

* In some situations, :command:`univention-radius-ntlm-auth` did neither correctly report
  errors to the :program:`RADIUS` server nor logged them. The program has been
  improved and is now able to intercept these errors and log them to
  :file:`/var/log/univention/radius_ntlm_auth.log` (:uv:bug:`58132`).

* The permissions for the log file :file:`/var/log/univention/radius_ntlm_auth.log`
  weren't set correctly by :program:`logrotate`,
  which caused :command:`univention-radius-ntlm-auth` to crash.
  This update automatically corrects the file permissions and
  the configuration of :program:`logrotate` (:uv:bug:`58132`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* Pre-create the AD built-in groups ``Pre-Windows 2000 Compatible Access``,
  ``Windows Authorization Access Group``, and ``IIS_IUSRS``
  through |UDM| in the join script.
  This is required,
  because Univention puts those groups on the :envvar:`connector/s4/mapping/group/ignorelist`,
  but Univention wants them to be defined with static POSIX IDs across the |UCS| domain.
  As a result, these groups are now created with the ``hidden`` flag,
  so they don't show up in UMC for new |UCS| domains.
  That's okay, because they aren't to be administrated in any way,
  they just allocate a POSIX ID. This update is a follow-up to :uv:kb:`18673` (:uv:bug:`53882`).

* Samba 4.21 had a regression
  where :command:`samba-tool domain trust create` failed to create the trust object.
  The upstream patch for Samba 4.22 has been ported back to fix this (:uv:bug:`58299`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* Add the AD built-in groups ``Pre-Windows 2000 Compatible Access``, ``Windows
  Authorization Access Group``, and ``IIS_IUSRS`` to the |UCSUCRV|
  :envvar:`connector/s4/mapping/group/ignorelist`. The first of these groups is
  relevant to control access to the attribute ``memberOf`` in Active Directory,
  for example for ``univention-s4search``. By default, it contains the virtual group
  ``Authenticated Users``, but may be configured differently in Samba/AD for
  security reasons. This update is a follow-up to :uv:kb:`18673` (:uv:bug:`53882`).

* Slight adjustments for the experimental delegative administration feature
  have been done (:uv:bug:`58432`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* Introduced the |UCSUCRV|
  :envvar:`connector/ad/mapping/allow-subtree-ancestors`,
  which, if enabled, allows the synchronization of ancestors of sub-trees allowed
  with the |UCSUCRVs| ``connector/ad/mapping/allowsubtree/.*/[ad|ucs]``.
  This can make the management
  of the selective synchronization of more complex LDAP DIT structures simpler.
  Additionally, when this new variable is enabled, a re-synchronization with one
  of the ``resync_object_from_*`` scripts will handle the re-synchronization of
  ancestors automatically if necessary (:uv:bug:`57979`).

* Slight adjustments for the experimental delegative administration feature
  have been done (:uv:bug:`58432`).

* In cases where customers chose LDAPS as protocol to bind to Active Directory,
  by setting the UCR variables ``connector/ad/ldap/port=636`` and ``connector/ad/ldap/ldaps=yes``,
  the script :command:`univention-adsearch` aborted with ``NT_STATUS_INVALID_PARAMETER_MIX``.
  Now it passes the parameters ``tls cafile`` and ``tls crlfile`` to :program:`ldbsearch`
  to avoid that error message (:uv:bug:`56139`).


.. _changelog-univention-net-install:

Univention PXE installation
======================================

* The UCS PXE Installation services provided by the package :program:`univention-net-installer` were deprecated
  and need to be removed before upgrading to UCS 5.2-4.

.. _changelog-other:

*************
Other changes
*************

* A new library for delegative administration has been introduced
  (:uv:bug:`58432`).

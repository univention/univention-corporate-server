.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _references-ucr-variables:

**********************
UCR variable reference
**********************

This section provides a reference for UCR variables.

.. envvar:: directory/manager/user_group/uniqueness

   If activated with the value ``true``
   or the variable isn't set,
   usernames and group names must be distinct.
   That means if there is a username ``test``,
   then Nubus doesn't allow a group with the name ``test``.

   For information where to this variable applies,
   see :ref:`ucs-operation-groups-management-tab-general-name`
   in :ref:`ucs-operation-groups-creation-assignment`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/properties/mailPrimaryAddress/required

   If activated with the value ``true``,
   the *User creation wizard* requires functional administrators
   to provide a primary email address when creating user accounts.

   For information about this requirement,
   see :ref:`iam-user-create-wizard-require-primary-email`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/disabled

   Controls whether the *User creation wizard*
   appears in the *Users* management module
   in the *Management UI*.
   When set to ``true``,
   Nubus deactivates the user creation wizard
   and displays the full user creation form instead.
   When unset or set to ``false``,
   the wizard appears.

   For information about using the user creation wizard,
   see :ref:`iam-user-create-wizard`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/disabled/default

   Sets the default value for the *Account disabled* checkbox
   in the *User creation wizard*.
   When set to ``true``,
   the wizard creates deactivated user accounts.
   When set to ``false``,
   the wizard creates activated user accounts.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/disabled/visible

   Controls whether the *Account disabled* checkbox
   appears in the *User creation wizard*.
   When set to ``true``,
   functional administrators can see the checkbox.
   When unset or set to ``false``,
   the checkbox doesn't appear.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/invite/default

   Sets the default value for the *Invite user via e-mail* checkbox
   in the *User creation wizard*.
   When set to ``true``,
   the checkbox is enabled by default for new user creation.
   When set to ``false``,
   the checkbox is disabled by default.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/invite/visible

   Controls whether the *Invite user via e-mail* checkbox
   appears in the *User creation wizard*.
   When set to ``true``,
   functional administrators can see the checkbox.
   When unset or set to ``false``,
   the checkbox doesn't appear.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/overridePWLength/default

   Sets the default value for the *Override password check* checkbox
   in the *User creation wizard*.
   When set to ``true``,
   the password quality and minimum length checks are bypassed by default.
   When set to ``false``,
   password checks are applied by default.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/overridePWLength/visible

   Controls whether the *Override password check* checkbox
   appears in the *User creation wizard*.
   When set to ``true``,
   functional administrators can see the checkbox.
   When unset or set to ``false``,
   the checkbox doesn't appear.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/pwdChangeNextLogin/default

   Sets the default value for the *User has to change password on next login* checkbox
   in the *User creation wizard*.
   When set to ``true``,
   users must change their password on the next sign-in by default.
   When set to ``false``,
   this requirement is not set by default.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/users/user/wizard/property/pwdChangeNextLogin/visible

   Controls whether the *User has to change password on next login* checkbox
   appears in the *User creation wizard*.
   When set to ``true``,
   functional administrators can see the checkbox.
   When unset or set to ``false``,
   the checkbox doesn't appear.

   For information about this property,
   see :ref:`iam-user-create-wizard-account-properties`.

   :Default value: not set
   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: directory/manager/web/modules/groups/group/checks/circular_dependency

   If activated with the value ``yes``
   or the variable isn't set,
   Nubus automatically detects cyclic dependencies of nested groups
   and refuses to create them.
   To deactivate the check,
   set it to the value ``no``.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-nested`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: dns/forwarder1

   You can configure external DNS servers to resolve hostnames and addresses
   outside the Nubus for UCS domain.
   The local domain DNS server automatically queries an external DNS server
   when it can't find an address in the local LDAP directory.
   This variable sets the first external DNS server.

   For information about configuring external DNS servers,
   see :ref:`system-administration-network-name-servers`.

   :Type: string


.. envvar:: dns/forwarder2

   This UCR variable sets the second external DNS server.
   For more details about the forwarder,
   see :envvar:`dns/forwarder1`.

   :Type: string


.. envvar:: dns/forwarder3

   This UCR variable sets the third external DNS server.
   For more details about the forwarder,
   see :envvar:`dns/forwarder1`.

   :Type: string


.. envvar:: gateway

   You need a gateway to send traffic to networks outside your local subnet.
   This variable sets the IPv4 address of the default gateway.
   A gateway you configure here takes priority over router advertisements.

   For information about configuring gateways,
   see :ref:`system-administration-network-gateway`.

   :Type: string


.. envvar:: grub/append

   Use this variable to pass additional options to the Linux kernel.
   For a complete list of available kernel parameters,
   see `Linux Kernel Parameters <https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html>`_.

   For more information about configuring the GRUB boot manager,
   see :ref:`system-administration-boot-manager-configuration`.

   :Default value: not set
   :Type: string


.. envvar:: grub/bootsplash

   Controls whether GRUB displays a graphical startup animation when your system boots.
   When set to ``splash``,
   GRUB displays the animation.
   When set to ``nosplash`` or unset,
   GRUB doesn't display an animation.

   For more information about configuring the GRUB boot manager,
   see :ref:`system-administration-boot-manager-configuration`.

   :Default value: not set
   :Possible values: ``splash``, ``nosplash``, not set
   :Type: string


.. envvar:: grub/gfxmode

   Specifies the graphical resolution for the boot menu.
   Use the format :samp:`{HORIZONTAL}x{VERTICAL}@{COLORDEPTHBIT}`,
   for example ``1024x768@16``.
   Your system's VESA BIOS supports only specific resolutions.

   For more information about available VESA modes,
   see `VESA BIOS Extensions <https://en.wikipedia.org/wiki/VESA_BIOS_Extensions>`_.

   For more information about configuring the GRUB boot manager,
   see :ref:`system-administration-boot-manager-configuration`.

   :Default value: ``800x600@16``
   :Type: string


.. envvar:: grub/timeout

   Specifies how long in seconds the boot menu waits for user input
   before GRUB boots the default kernel.
   When you set this to ``0``,
   GRUB boots the default kernel immediately.
   When you set this to ``-1``,
   you must select the kernel manually.

   For more information about configuring the GRUB boot manager,
   see :ref:`system-administration-boot-manager-configuration`.

   :Default value: ``5``
   :Possible values: integer, ``0`` for immediate boot, ``-1`` for manual selection
   :Type: integer

.. envvar:: interfaces/*/address

   Configure the IPv4 address for a network interface.
   The variable name follows the pattern :samp:`interfaces/{INTERFACE}/address`,
   for example :samp:`interfaces/eth0/address`.
   If you want to use DHCP,
   don't set this variable.
   See :envvar:`interfaces/*/type` for dynamic assignment.

   For information about configuring IPv4 addresses,
   see :ref:`system-administration-network-ipv4`.

   :Type: string


.. envvar:: interfaces/*/ipv6/acceptRA

   Enable Stateless Address Autoconfiguration (SLAAC) for a network interface.
   When you activate this option,
   routers on the local network segment assign the IPv6 address.
   The variable name follows the pattern :samp:`interfaces/{INTERFACE}/ipv6/acceptRA`,
   for example :samp:`interfaces/eth0/ipv6/acceptRA`.

   For information about configuring IPv6 addresses,
   see :ref:`system-administration-network-ipv6`.

   :Type: boolean


.. envvar:: interfaces/*/ipv6/address

   Configure a static IPv6 address for a network interface.
   The variable name follows the pattern
   :samp:`interfaces/{INTERFACE}/ipv6/{IDENTIFIER}/address`,
   for example :samp:`interfaces/eth0/ipv6/default/address`.
   Use ``default`` for the primary address;
   you can use functional names like ``mail`` or ``web`` for additional addresses.
   If you want to use SLAAC,
   don't set this variable.
   See :envvar:`interfaces/*/ipv6/acceptRA` for automatic configuration.

   For information about configuring IPv6 addresses,
   see :ref:`system-administration-network-ipv6`.

   :Type: string


.. envvar:: interfaces/*/ipv6/prefix

   Configure the IPv6 prefix length in CIDR notation for a network interface.
   The variable name follows the pattern
   :samp:`interfaces/{INTERFACE}/ipv6/{IDENTIFIER}/prefix`,
   for example :samp:`interfaces/eth0/ipv6/default/prefix`.
   If you want to use SLAAC,
   don't set this variable.
   See :envvar:`interfaces/*/ipv6/acceptRA` for automatic configuration.

   For information about configuring IPv6 addresses,
   see :ref:`system-administration-network-ipv6`.

   :Type: string
   :Possible values: ``0`` to ``128``


.. envvar:: interfaces/*/netmask

   Configure the network mask for a network interface.
   The variable name follows the pattern :samp:`interfaces/{INTERFACE}/netmask`,
   for example :samp:`interfaces/eth0/netmask`.

   For information about configuring IPv4 addresses,
   see :ref:`system-administration-network-ipv4`.

   :Type: string


.. envvar:: interfaces/*/setting

   Configure arbitrary settings for a network interface.
   The variable name follows the pattern :samp:`interfaces/{INTERFACE}/{SETTING}`,
   where :samp:`{SETTING}` can be any of the supported interface configuration options.

   Common settings include:

   * :envvar:`interfaces/*/address` — IPv4 address
   * :envvar:`interfaces/*/netmask` — Network mask
   * :envvar:`interfaces/*/type` — Type of IP assignment
   * :envvar:`interfaces/*/ipv6/address` — IPv6 address
   * :envvar:`interfaces/*/ipv6/prefix` — IPv6 prefix length
   * :envvar:`interfaces/*/ipv6/acceptRA` — Enable SLAAC

   You can define virtual interfaces using the same pattern with a numeric suffix.
   For example,
   virtual interfaces use the naming convention ``eth0_1``, ``eth0_2``, and so on.
   In the network interface listing,
   these appear with colons instead of underscores,
   such as ``eth0:1`` and ``eth0:2``.
   This allows one network card to have multiple independent configurations and IP addresses.

   For information about configuring network interfaces,
   see :ref:`system-administration-network-ipv4` and :ref:`system-administration-network-ipv6`.

   :Type: depends on setting


.. envvar:: interfaces/*/type

   Define the type of IP assignment for a network interface.
   The variable name follows the pattern :samp:`interfaces/{INTERFACE}/type`,
   for example :samp:`interfaces/eth0/type`.

   Choose from the following values:

   ``static``
      Configure the interface with static values
      from additional variables like :envvar:`interfaces/*/address`.

   ``dhcp``
      Enable dynamic assignment over DHCP.

   ``manual``
      Require manual configuration.

   For information about configuring IPv4 addresses,
   see :ref:`system-administration-network-ipv4`.

   :Type: string
   :Possible values: ``static``, ``dhcp``, ``manual``


.. envvar:: ipv6/gateway

   You can configure an IPv6 gateway.
   For IPv6,
   you must enter a gateway in static configuration;
   for dynamic configuration,
   it's optional but recommended.
   A gateway you configure here takes priority over router advertisements,
   which might otherwise change the route.
   You can append a zone index with a percent sign (%)
   to specify the interface this address is reachable from.

   For information about configuring IPv6 gateways,
   see :ref:`system-administration-network-gateway`.

   :Type: string


.. envvar:: kernel/blacklist

   Use this variable to prevent specific kernel modules from loading automatically.
   The system automatically detects and loads required drivers (kernel modules).
   You can use this variable to exclude modules that you don't want the system to load.
   If you need to blacklist multiple modules,
   separate them with a semicolon.

   For information about kernel module configuration,
   see :ref:`system-administration-kernel-modules-detection`.

   :Default value: not set
   :Possible values: semicolon-separated list of module names
   :Type: list


.. envvar:: kernel/modules

   Use this variable to load kernel modules that the system doesn't automatically detect.
   The system automatically detects and loads required drivers (kernel modules).
   You can use this variable to load modules that the system can't automatically detect.
   If you need to load multiple modules,
   separate them with a semicolon.

   For information about kernel module configuration,
   see :ref:`system-administration-kernel-modules-detection`.

   :Default value: not set
   :Possible values: semicolon-separated list of module names
   :Type: list


.. envvar:: ldap/master

   Contains the fully qualified domain name of the domain's Primary Directory Node.

   :Type: string


.. envvar:: local/repository

   Activates and deactivates the local repository.
   When activated with the value ``yes``,
   the system uses a locally maintained repository for package updates and installations.
   This is useful in environments with multiple systems
   to reduce bandwidth consumption and enable offline updates.

   For information about creating and maintaining a local repository,
   see :ref:`lifecycle-local-repository-create-init`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: nameserver1

   Set the first DNS server the system uses for name resolution.

   For information about configuring name servers,
   see :ref:`system-administration-network-name-servers`.

   :Type: string


.. envvar:: nameserver2

   Set the second DNS server the system uses for name resolution.
   For details about the name server,
   see :envvar:`nameserver1`.

   :Type: string


.. envvar:: nameserver3

   Set the third DNS server the system uses for name resolution.
   For details about the name server,
   see :envvar:`nameserver1`.

   :Type: string


.. envvar:: nss/group/cachefile

   If activated,
   Nubus exports all group data to a cache file.
   The NSS module *extrausers* includes the exported data.
   This results to significant performance improvements in large environments.
   If the variable isn't set, the cache file is activated.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Default value: ``yes``
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: nss/group/cachefile/check_member

   If activated, the group cache export verifies
   whether the exported group members are still present in the LDAP directory.
   If you only use user management methods through the *Users* and *Groups* management module,
   this validation isn't necessary and you can deactivate it.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Possible values: ``true``, ``false``, not set
   :Type: boolean

.. envvar:: nss/group/cachefile/invalidate_interval

   If Nubus uses the group cache file, see :envvar:`nss/group/cachefile` UCR variable,
   Nubus exports the group data to the cache file in the interval specified here.
   The interval is in cron format, see :command:`man 5 crontab`
   or `crontab(5) <https://manpages.debian.org/bookworm/cron/crontab.5.en.html>`_.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Type: cron

.. envvar:: nss/group/cachefile/invalidate_on_changes

   If Nubus has this variable activated and the group cache file has been enabled,
   see the :envvar:`nss/group/cachefile` UCR variable,
   the Nubus automatically regenerates the cache file
   whenever a domain administrator edits a group in the *Management UI*.
   If this variable isn't set, the functionality is enabled.

   For information about where this variable applies,
   see :ref:`ucs-operation-groups-management-cache`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: password/quality/credit/digits

   Defines the minimum required number of digits for passwords.
   A newly defined password must include at least this many digits.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/lower

   Defines the minimum required number of lowercase letters for passwords.
   A newly defined password must include at least this many lowercase letters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks, including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/other

   Defines the minimum required number of characters in the user password
   that are neither letters nor digits.
   A newly defined password must include at least this many characters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/credit/upper

   Defines the minimum required number of uppercase letters for passwords.
   A newly defined password must include at least this many uppercase letters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: integer

.. envvar:: password/quality/forbidden/chars

   Defines the characters and digits
   that aren't allowed in passwords.
   A newly defined password must not contain these characters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string


.. envvar:: password/quality/length/min

   When changing passwords through *Univention Portal*, *Management UI*,
   *Directory Manager* or Kerberos without Samba,
   UCS checks whether the new password meets the minimum length requirement.

   You can define the minimum length through the following approaches:

   * Use this UCR variable to define the minimum password length locally per Nubus for UCS node.
     The value applies to all user accounts.

   * You can use *Policy: Passwords*, type ``policies/pwhistory``,
     to override the value defined in this UCR variable.
     The values of the policy apply to user accounts
     that are subject to the policy.
     The policy takes precedence over the UCR variable.

     If the policy has *Password quality check* activated,
     :program:`python-cracklib` demands a minimum password length of 4 characters.

   The UCR variable can have the following values:

   * Integer to define the minimum password length as number of characters.

   * The value ``yes`` applies checks from :program:`python-cracklib`.

   * The value ``sufficient`` doesn't include :program:`python-cracklib` checks.

   :Default value: not set
   :Type: string

   .. seealso::

      :ref:`password-management-policies`
         for context information about password policies in Nubus for UCS.

      :external+uv-nubus-manual:ref:`nubus-user-password-management-module`
         in :cite:t:`uv-nubus-manual`
         for information about *Policy: Passwords* in the *Policies module* in the *Management UI*.


.. envvar:: password/quality/required/chars

   Defines individual characters as required for passwords.
   A newly defined password must include the specified characters.

   If the password policy has the option *Password quality check* activated,
   Nubus runs additional checks including dictionary checks,
   for password changes in *Management UI* (UMC), Samba, and Kerberos.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string


.. envvar:: password/quality/mspolicy

   Defines the standard Microsoft password complexity criteria.

   The values ``yes``, ``1``, or ``true``
   activate the standard Microsoft password complexity criteria
   in addition to the other criteria validated with :program:`python-cracklib`.
   The value ``sufficient`` only applies the standard Microsoft password complexity criteria
   without :program:`python-cracklib`.
   The default value is unset and corresponds to the value ``false``.

   For more information,
   see :ref:`password-management-policies`.

   :Default value: not set
   :Type: string

.. envvar:: pkgdb/scan

    Controls whether Nubus for UCS systems report software installations
    to the software monitor.
    When activated with the value ``yes``
    or the variable isn't set,
    the system tracks software installations, deinstallations, and updates
    in the software monitor database.
    When set to ``no``,
    the system doesn't record software changes in the software monitor.

    For information about temporarily deactivating monitoring,
    see :ref:`lifecycle-software-monitor-configuration`.
    For information about the software monitor,
    see :ref:`lifecycle-software-monitor`.

    :Default value: not set
    :Possible values: ``yes``, ``no``, not set
    :Type: boolean


.. envvar:: portal/auth-mode

   Specifies the mechanism
   that the *Portal* uses to authenticate a user
   when clicking the :guilabel:`Login` in the *Portal* sidebar.
   For the values ``saml`` and ``oidc``
   the clients have to resolve the name of the single sign-on server
   and retrieve a trustworthy and valid certificate.

   :Default value: ``ucs``
   :Type: string
   :Possible values: ``saml``, ``oidc``, ``ucs``


.. envvar:: portal/reload-tabs-on-logout

   If activated,
   the *Management UI* sets up a persistent connection
   to the user's web browser.
   It notifies all Univention Portal browser tabs of a sign-out
   and causes them to reload.

   :Default value: ``false``
   :Type: boolean


.. envvar:: proxy/http

   The system uses this HTTP proxy server for HTTP connections.
   Enter the proxy URL, including the port and authentication credentials when needed.

   Examples:

   * Without authentication: :samp:`http://192.168.1.100:3128`
   * With authentication: :samp:`http://{<Username>}:{<Password>}@192.168.1.100:3128`

   When you set this variable,
   the system creates an ``http_proxy`` environment variable
   in :file:`/etc/profile`
   for use by command line tools and system utilities.

   For information about proxy configuration,
   see :ref:`system-administration-proxy-configuration`.

   :Default value: not set
   :Type: string

.. envvar:: proxy/https

   The system uses this proxy server for HTTPS connections.
   Provide a proxy URL,
   optionally including port and authentication credentials.

   Examples:

   * Without authentication: :samp:`https://192.168.1.100:3128`
   * With authentication: :samp:`https://{<Username>}:{<Password>}@192.168.1.100:3128`

   When you set this variable,
   the system creates an ``https_proxy`` environment variable
   in :file:`/etc/profile`
   for use by command line tools and system utilities.
   If you don't set :envvar:`proxy/https`,
   the system uses :envvar:`proxy/http` for HTTPS connections.

   For information about proxy configuration,
   see :ref:`system-administration-proxy-configuration`.

   :Default value: not set
   :Type: string

.. envvar:: proxy/no_proxy

   A comma-separated list of domain names that bypass the proxy.

   Example: :samp:`localhost,127.0.0.1,internal.example.com`

   Subdomains inherit proxy exclusions from parent domains.
   For example, if you exclude ``example.com``,
   the system also excludes ``mail.example.com`` and ``www.example.com``.

   For information about excluding domains from proxy access,
   see :ref:`system-administration-proxy-exclusions`.

   :Default value: not set
   :Type: comma-separated list of strings


.. envvar:: repository/mirror/basepath

   Specifies the base directory where the local repository mirror is stored.
   The directory is used by the :command:`univention-repository-create`
   and :command:`univention-repository-update` commands
   to store mirrored packages and repository metadata.

   For information about managing disk space in local repositories,
   see :ref:`lifecycle-local-repository-maintenance-disk-space`.

   :Default value: ``/var/lib/univention-repository``
   :Type: string


.. envvar:: repository/mirror/server

   Specifies the upstream repository server
   from which the local mirror retrieves packages and updates.
   The value must be a fully qualified domain name or IP address.

   For information about configuring a local repository to use a different upstream server,
   see :ref:`lifecycle-local-repository-create-multiple-locations`.

   :Default value: ``https://updates.software-univention.de``
   :Type: string


.. envvar:: repository/mirror/sources

   Controls whether the local repository mirror includes source packages.
   When activated with the value ``yes``,
   the mirror downloads and stores source packages in addition to binary packages.
   Deactivating this variable reduces the storage space required for the mirror.

   For information about managing disk space in local repositories,
   see :ref:`lifecycle-local-repository-maintenance-disk-space`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

.. envvar:: repository/mirror/version/end

   If the mirroring of the repository is active,
   see :envvar:`local/repository`,
   this variable is set each time
   to the UCS version which was last retrieved from the mirror.

   :Default value: not set, uses current system version
   :Type: string

.. envvar:: repository/mirror/version/start

   If the mirroring of the repository is active,
   see :envvar:`local/repository`,
   this variable configures the lowest UCS version
   which is retrieved from the mirror.

   For information about major versions,
   see :ref:`lifecycle-versioning-release-types-major`.

   :Default value: not set, uses current major version
   :Type: string


.. envvar:: repository/online/component/.*/unmaintained

   Controls whether to allow installation of unmaintained packages from additional repositories.
   When activated with the value ``yes``,
   the system permits installation of packages marked as unmaintained
   from non-official repository components.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean

   .. deprecated:: UCS 5.0-3

      This variable is **deprecated since UCS 5.0-3**.
      The *Univention Configuration Registry* management module
      in the *Management UI*.
      Don't use it in new configurations.

   Impact on existing configurations
       If you have this variable set in your UCR configuration,
       the system silently ignores it.
       The system only uses the *maintained* branch
       for all repository components.

   Primary alternative
       Use component-specific configuration
       through :envvar:`repository/online/component/COMPONENTNAME`
       to enable or disable entire components.
       This is the recommended and simplest migration path.

       **Example:** To deactivate the optional component :samp:`{MYCOMPONENT}`,
       set :samp:`repository/online/component/{MYCOMPONENT}` to ``no``.

   Advanced alternative
       For more granular control,
       you can use :samp:`repository/online/component/{COMPONENTNAME}/server`
       to point to a custom repository
       that only provides the packages you need.


.. envvar:: repository/online/component/COMPONENTNAME

   Enables or disables a specific repository component.
   Set the variable to ``no`` to exclude the component from synchronization.
   Leave the variable unset to use the default behavior.

   :samp:`{COMPONENTNAME}` is a placeholder for the actual component name.
   Multiple components can be configured by using different :samp:`{COMPONENTNAME}` values.

   .. note::

      This variable is the recommended replacement
      for the deprecated :envvar:`repository/online/component/.*/unmaintained`
      variable, which is no longer available since UCS 5.0-3.

   For information about excluding optional components,
   see :ref:`lifecycle-local-repository-maintenance-disk-space`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: repository/online/server

   Specifies the repository server URL used for online package updates and installations.
   The value must be a fully qualified URL pointing to a valid APT repository.

   For information about configuring the repository server,
   see :ref:`lifecycle-local-repository-configuration`.

   :Default value: ``https://updates.software-univention.de``
   :Type: string

.. envvar:: saml/idp/selfservice/check_email_verification

   If activated,
   users that have registered themselves
   through the :program:`Self Service` app
   need to verify their email address first
   before they can sign in.

   You must set this UCR variable
   on the :term:`UCS Primary Directory Node`
   and all :term:`UCS Backup Directory Node`\s.
   The variable has no effect on accounts
   created by user accounts from the ``Domain Admins`` group.

   For more information,
   see :ref:`end-user-self-service-registration-account-activation`.

   :Default value: ``false``
   :Type: boolean


.. envvar:: server/role

   Contains the system role of the system.
   You can't change this setting after a domain join.

   For information about system roles,
   see :ref:`domain-infrastructure-system-roles`.

   :Type: string


.. envvar:: ucs/web/theme

   Specifies the name of the theme to apply to all web interfaces
   such as the login page, the portal, and the *Management UI*.
   The value corresponds to a CSS file of the same name
   in the folder :file:`/usr/share/univention-web/themes/`.

   For information about switching between themes, creating custom themes,
   and applying changes, see :ref:`management-interface-theming`.

   :Default value: ``dark``
   :Type: string
   :Possible values: ``light``, ``dark``, or custom theme names


.. envvar:: umc/http/processes

   Defines the number of *UMC Server* processes
   that Nubus for UCS starts in parallel.

   :Default value: ``1``
   :Type: Unsigned integer


.. envvar:: umc/http/session/timeout

   The web browser automatically closes the browser session
   after the defined time period in seconds.
   A new session requires a new sign-in

   :Default value: ``300``
   :Type: Unsigned integer


.. envvar:: umc/oidc/issuer

   Defines the OpenID provider issuer of this relying party entry.

   :Default value: not set
   :Type: string


.. envvar:: umc/oidc/rp/server

   Defines the fully qualified domain name of the relying party for the *UMC Server*.
   If the variable is unset,
   Nubus for UCS uses the fully qualified domain name of the UCS system and all IP addresses.

   :Default value: not set
   :Type: string


.. envvar:: umc/web/oidc/enabled

   If activated, the *UMC Server* tries the sign-in
   through OpenID Connect single sign-on
   before using a regular sign-in.

   :Default value: ``true``
   :Type: boolean


.. envvar:: umc/web/sso/enabled

   If activated, the *UMC Server* tries the sign-in
   through SAML single sign-on
   before using a regular sign-in.

   :Default value: not set
   :Type: boolean

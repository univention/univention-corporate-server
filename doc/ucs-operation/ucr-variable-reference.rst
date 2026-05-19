.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _references-ucr-variables:

**********************
UCR variable reference
**********************

This section provides a reference for UCR variables.

.. envvar:: auth/faillog

   Controls whether Nubus for UCS automatically locks user accounts
   after too many failed sign-in attempts.
   When set to ``yes``,
   the lockout mechanism is active.
   When unset,
   the lockout mechanism is inactive.

   Configure the number of failed attempts that trigger the lockout
   in :envvar:`auth/faillog/limit`.

   For information about configuring the PAM stack lockout,
   see :ref:`iam-user-lockout-pam`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: auth/faillog/limit

   Sets the number of failed sign-in attempts
   that trigger an automatic account lockout.
   This variable has effect only
   when :envvar:`auth/faillog` is set to ``yes``.

   For information about configuring the PAM stack lockout,
   see :ref:`iam-user-lockout-pam`.

   :Default value: ``5``
   :Type: integer


.. envvar:: auth/faillog/lock_global

   Controls whether Nubus for UCS stores account lockouts
   globally in the LDAP directory
   instead of locally on each system.
   When set to ``yes``,
   a lockout on one system applies to all systems in the domain.
   When unset,
   lockouts apply only to the local system.

   You can set this variable only on
   :term:`Primary Directory Node` or :term:`Backup Directory Node` systems,
   because other system roles lack write permissions in the LDAP directory.

   For information about configuring the PAM stack lockout,
   see :ref:`iam-user-lockout-pam`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: auth/faillog/root

   Controls whether the automatic account lockout
   also applies to the ``root`` user account.
   By default,
   Nubus for UCS exempts ``root`` from the lockout mechanism.
   When set to ``yes``,
   the lockout applies to ``root`` as well.

   For information about configuring the PAM stack lockout,
   see :ref:`iam-user-lockout-pam`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: auth/faillog/unlock_time

   Sets the time in seconds
   after which Nubus for UCS automatically unlocks a locked account.
   When unset,
   the lockout has no time limit
   and an administrator must unlock the account manually.
   When set to ``0``,
   Nubus for UCS resets the lockout counter immediately.

   For information about configuring the PAM stack lockout,
   see :ref:`iam-user-lockout-pam`.

   :Default value: not set
   :Possible values: integer (seconds), ``0`` for immediate counter reset, not set
   :Type: integer


.. envvar:: ldap/base

   Contains the base distinguished name (DN) of the LDAP directory.
   The base DN defines the root of the directory tree
   and serves as the search base for LDAP queries across the domain.
   The installer sets this value during the installation of the Primary Directory Node.
   You can't change it afterward.

   .. note::

      Nubus for UCS sets this variable automatically during installation.
      Don't change it manually.

   :Default value: not set
   :Type: string


.. envvar:: ldap/policy/cron

   Specifies when Nubus for UCS synchronizes UCR policy variables
   from the LDAP directory to the local system.
   UCR policies set in the directory service take effect
   on the local system after the next synchronization.
   Use standard cron schedule syntax.
   For the syntax, run :command:`man 5 crontab`.

   For information about UCR policies,
   see :ref:`system-administration-ucr-policy`.

   :Default value: ``5 * * * *``
   :Type: cron


.. envvar:: ldap/ppolicy/enabled

   Controls whether the :program:`OpenLDAP` ``ppolicy`` overlay is active
   on the local system.
   When set to ``yes``,
   the LDAP server monitors bind attempts
   according to the settings in the ``pwdPolicy`` object in the LDAP directory.
   After you set this variable,
   restart the ``slapd`` service for the change to take effect.

   This variable is available on
   :term:`Primary Directory Node` and :term:`Backup Directory Node` systems only.

   For information about configuring the OpenLDAP lockout,
   see :ref:`iam-user-lockout-openldap`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: directory/manager/blocklist/cleanup/cron

   Specifies when the cleanup script runs
   to lift expired block list entries.
   The script removes entries whose retention time has elapsed.
   Use standard cron schedule syntax.
   For the syntax, run :command:`man 5 crontab`.

   For the block list feature this variable depends on,
   see :envvar:`directory/manager/blocklist/enabled`.

   For general information about the *Blocklists* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-blocklists`
   in :cite:t:`uv-nubus-manual`.

   :Default value: ``0 8 * * *``
   :Type: cron


.. envvar:: directory/manager/blocklist/enabled

   Controls whether Nubus for UCS automatically blocks property values
   removed from a UDM object,
   preventing them from being reused on other objects.
   When set to ``false``,
   the block list feature is inactive.

   Configure the cleanup schedule with
   :envvar:`directory/manager/blocklist/cleanup/cron`.

   For general information about the *Blocklists* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-blocklists`
   in :cite:t:`uv-nubus-manual`.

   :Default value: ``false``
   :Possible values: ``true``, ``false``
   :Type: boolean


.. envvar:: directory/manager/mail-address/uniqueness

   Controls whether alternative email addresses must also be globally unique.
   When unset,
   only the primary email address must be unique across the domain.
   When set to ``true``,
   alternative email addresses must also be unique
   and can't overlap with any primary email address.

   :Default value: ``false``
   :Possible values: ``true``, ``false``
   :Type: boolean


.. envvar:: directory/manager/templates/alphanum/whitelist

   Specifies additional characters to preserve
   when the UDM object template option ``<:alphanum>`` is applied.
   By default,
   ``<:alphanum>`` removes all characters that aren't letters or digits.
   Characters listed in this variable are exempt from removal.

   :Default value: not set
   :Type: string


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

.. envvar:: directory/reports/cleanup/age

   Specifies the maximum age of a report file in seconds
   before the cleanup cron job removes it.
   If the variable is unset,
   the system uses a default of ``43200`` seconds (12 hours).

   For information about configuring report cleanup,
   see :ref:`management-interface-directory-reports-create-umc`.

   :Default value: ``43200``
   :Type: integer


.. envvar:: directory/reports/cleanup/cron

   Specifies when the cron job runs to remove expired report files.
   Use standard cron schedule syntax.
   For the syntax, run :command:`man 5 crontab`.
   The cleanup job removes reports that exceed the age
   configured in :envvar:`directory/reports/cleanup/age`.

   For information about configuring report cleanup,
   see :ref:`management-interface-directory-reports-create-umc`.

   :Default value: ``0 0 * * *``
   :Type: cron


.. envvar:: directory/reports/logo

   Specifies the path to an image file
   to use as the logo in the header of PDF reports.
   You can use common image formats such as JPEG, PNG, and GIF.
   The system scales the image to a fixed width of 5.0 cm.

   For information about customizing report appearance,
   see :ref:`management-interface-directory-reports-customize`.

   :Default value: ``/usr/share/univention-directory-reports/univention_logo.png``
   :Type: string

.. envvar:: directory/reports/templates/csv/.*

   Registers a CSV report template for a specific object type.
   The variable name follows the pattern
   :samp:`directory/reports/templates/csv/{NAME}`,
   where :samp:`{NAME}` is an arbitrary identifier, for example ``user1``.

   The value consists of four space-separated fields:

   .. code-block:: none

      <module> "<report name>" <directory> <template file>

   ``<module>``
      The UDM module the report applies to,
      for example ``users/user``, ``groups/group``, or ``computers/computer``.

   ``"<report name>"``
      The display name shown in the management module.
      Enclose the name in double quotes.

   ``<directory>``
      The path to the directory containing the template file.

   ``<template file>``
      The CSV template filename relative to ``<directory>``.

   Example:

   .. code-block:: none

      users/user "CSV Report" /etc/univention/directory/reports/default users.csv

   For information about creating and registering report templates,
   see :ref:`management-interface-directory-reports-customize`.

   :Default value: not set
   :Type: string


.. envvar:: directory/reports/templates/pdf/.*

   Registers a PDF report template for a specific object type.
   The variable name follows the pattern
   :samp:`directory/reports/templates/pdf/{NAME}`,
   where :samp:`{NAME}` is an arbitrary identifier, for example ``user1``.

   The value consists of four space-separated fields:

   .. code-block:: none

      <module> "<report name>" <directory> <template file>

   ``<module>``
      The UDM module the report applies to,
      for example ``users/user``, ``groups/group``, or ``computers/computer``.

   ``"<report name>"``
      The display name shown in the management module.
      Enclose the name in double quotes.

   ``<directory>``
      The path to the directory containing the template file.
      The system resolves the actual template file from a language-specific subdirectory
      of ``<directory>``, for example :file:`de_DE/` or :file:`en_US/`.
      If no language subdirectory exists,
      it loads the template directly from ``<directory>``.

   ``<template file>``
      The template filename relative to the resolved directory.
      Use ``.rml`` files for RML-based PDF reports
      and ``.tex`` files for LaTeX-based PDF reports.

   Example:

   .. code-block:: none

      users/user "PDF Document" /etc/univention/directory/reports/default users.rml

   For information about creating and registering report templates,
   see :ref:`management-interface-directory-reports-customize`.

   :Default value: not set
   :Type: string


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


.. envvar:: kerberos/adminserver

   Specify which system serves as the Kerberos admin server.
   The Kerberos admin server runs on the Primary Directory Node
   and manages the administrative settings of the domain.

   For information about configuring the Kerberos administration server,
   see :ref:`domain-infrastructure-kerberos-administration-server`.

   :Type: string

.. envvar:: kerberos/defaults/dns_lookup_kdc

   Control whether the system queries DNS service records for Kerberos KDC servers.
   When you set this variable to ``true`` or leave it unset,
   the system reads the KDC(s) from DNS service records.
   Set it to ``false`` to disable DNS lookup,
   in which case you must configure the KDC(s) through the :envvar:`kerberos/kdc` variable.

   For information about configuring the Kerberos KDC,
   see :ref:`domain-infrastructure-kerberos-kdc`.

   :Default value: not set, equivalent to ``true``
   :Possible values: ``true``, ``false``, not set
   :Type: string


.. envvar:: kerberos/kdc

   Specify a list of Kerberos KDC servers.
   Use fully qualified domain names (FQDN) for the hostnames
   and separate multiple values with a blank.
   If you don't set this variable,
   the system queries DNS service records for the KDC,
   see :envvar:`kerberos/defaults/dns_lookup_kdc`.

   For information about overriding the KDC for a specific system,
   see :ref:`domain-infrastructure-kerberos-kdc`.

   :Type: string


.. envvar:: kerberos/realm

   Contains the name of the Kerberos realm,
   which is the common Kerberos trust context of a domain.
   The installer sets this value during the installation of the Primary Directory Node,
   and you cannot change it afterward.

   For information about configuring the Kerberos realm,
   see :ref:`domain-infrastructure-kerberos-realm`.

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


.. envvar:: ldap/overlay/lastbind

   Controls whether the :program:`OpenLDAP` ``lastbind`` overlay module is active.
   When set to ``yes``,
   the overlay records the timestamp of the last successful LDAP bind
   in the ``authTimestamp`` attribute of the user account.
   To limit how often the overlay writes to the attribute,
   configure :envvar:`ldap/overlay/lastbind/precision`.
   After you set this variable,
   restart the ``slapd`` service for the change to take effect.

   For information about activating the overlay and its prerequisites,
   see :ref:`iam-last-bind-activate`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: ldap/overlay/lastbind/precision

   Sets the minimum time in seconds
   between updates to the ``authTimestamp`` attribute
   by the :program:`OpenLDAP` ``lastbind`` overlay module.
   When the stored timestamp isn't older than this value,
   the overlay skips the update.
   When unset,
   the overlay updates ``authTimestamp`` on every successful LDAP bind.
   After you set this variable,
   restart the ``slapd`` service for the change to take effect.

   For information about the overlay module and this variable,
   see :ref:`iam-last-bind-activate`.

   :Default value: ``3600``
   :Type: integer


.. envvar:: ldap/pw-bcrypt

   Controls whether the :program:`OpenLDAP` server supports the bcrypt password hashing scheme.
   Set this variable to ``true`` to enable bcrypt as a password hashing method for user accounts.
   You must set this variable on all LDAP servers in your domain.

   When you leave this variable unset or set it to ``false``,
   the bcrypt password hashing module does not load in OpenLDAP.
   Users cannot authenticate with bcrypt password hashes.

   For information about enabling bcrypt password hashing,
   see :ref:`password-management-hashes-bcrypt`.

   :Default value: false
   :Possible values: ``true``, ``false``
   :Type: boolean


.. envvar:: listener/debug/level

   Sets the verbosity of log messages
   that the Univention Directory Listener writes to
   :file:`/var/log/univention/listener.log`.
   Each level includes all messages from less-severe levels.
   When unset,
   the Listener logs only error messages.

   .. _ucr-reference-debug-levels-listener-notifier:

   Debug levels for listener and notifier
      :``0``: Error messages only.
      :``1``: Warnings.
      :``2``: Process messages.
      :``3``: Informational messages.
      :``4``: Debug messages.
      :``5``: Trace messages (most verbose).

   For information about reading log files and setting the debug level,
   see :ref:`listener-notifier-troubleshooting-logfiles`.

   :Default value: not set, equivalent to ``0``
   :Possible values: ``0`` to ``5``
   :Type: integer


.. envvar:: listener/shares/rename

   Controls whether Nubus moves the content of a NFS or CIFS share
   when its storage path changes.
   When activated,
   Nubus moves the existing directory content to the new path.
   When unset or deactivated,
   Nubus creates a new empty directory at the new path
   and leaves the existing content at the old path.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


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


.. envvar:: mail/dovecot/auth/cache_negative_ttl

   Sets the time-to-live for negative authentication results in Dovecot,
   such as when a user isn't found or a password doesn't match.
   When set to ``0``,
   Dovecot doesn't cache negative results.

   For the TTL of successful :spelling:word:`lookups`,
   see :envvar:`mail/dovecot/auth/cache_ttl`.

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   :Default value: ``1 mins``
   :Type: string


.. envvar:: mail/dovecot/auth/cache_ttl

   Sets the time-to-live for cached authentication data in Dovecot.
   After the TTL expires,
   Dovecot no longer uses the cached record,
   except when the LDAP lookup fails with an internal error.

   For the TTL of negative results,
   see :envvar:`mail/dovecot/auth/cache_negative_ttl`.

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   :Default value: ``5 mins``
   :Type: string


.. envvar:: mail/dovecot/mailbox/delete

   Controls whether Dovecot deletes a user's IMAP mailbox
   when the corresponding user account is deleted.
   When activated,
   Dovecot removes the mailbox together with the account.
   When unset or deactivated,
   the mailbox is retained after the account is deleted.

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: mail/dovecot/mailbox/rename

   Controls whether Dovecot renames a user's IMAP mailbox
   when the user's primary email address changes.
   The mailbox name is linked to the primary email address,
   not to the username.
   When activated,
   Dovecot renames the mailbox to match the new primary email address.

   .. caution::

      When unset or deactivated,
      the mailbox retains the old name
      and the user can no longer access their previous emails
      after the primary email address changes.

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: mail/hosteddomains

   Contains the mail domains configured in the Nubus for UCS domain.
   Nubus sets this variable automatically
   when you create or remove mail domains
   through the *Mail* module in the *Management UI*.

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   .. note::

      Don't set this variable directly.
      Manage mail domains through the *Management UI* instead.

   :Default value: not set
   :Type: string


.. envvar:: mail/postfix/policy/listfilter

   Controls whether Postfix enforces sender restrictions
   for mail groups and mailing lists configured in the *Management UI*.
   When activated,
   only permitted senders can write to those groups and lists.
   When unset,
   any user can send to mail groups and mailing lists.

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   :Default value: not set
   :Possible values: ``yes``, ``no``, not set
   :Type: boolean


.. envvar:: mail/relayhost

   Specifies the mail relay server
   that Postfix uses to forward outgoing email to non-local addresses.
   When unset,
   Postfix resolves the responsible mail server directly
   by querying the MX record in DNS.
   When set,
   Postfix forwards all outgoing email to this server,
   which then handles further delivery.
   Enter the server as a fully qualified domain name (FQDN).

   For general information about the *Mail* management module,
   see :external+uv-nubus-manual:ref:`nubus-domain-mail`
   in :cite:t:`uv-nubus-manual`.

   :Default value: not set
   :Type: string


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


.. envvar:: notifier/debug/level

   Sets the verbosity of log messages
   that the Univention Directory Notifier writes to
   :file:`/var/log/univention/notifier.log`.
   Each level includes all messages from less-severe levels.
   When unset,
   the Notifier logs only error messages.

   For the debug levels,
   see :ref:`ucr-reference-debug-levels-listener-notifier`.

   For information about reading log files and setting the debug level,
   see :ref:`listener-notifier-troubleshooting-logfiles`.

   :Default value: not set, equivalent to ``0``
   :Possible values: ``0`` to ``5``
   :Type: integer


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

.. envvar:: password/hashing/bcrypt

   Controls whether Nubus for UCS uses bcrypt for hashing user passwords in the directory service.
   When you set this variable to ``true``,
   Nubus hashes new or changed user passwords with bcrypt instead of the default SHA-512 algorithm.
   Existing passwords keep their original hashing algorithm.
   Only new passwords use the new algorithm.

   You must set :envvar:`ldap/pw-bcrypt` to ``true`` on all LDAP servers
   before you activate this variable.

   Nubus for UCS limits bcrypt passwords to a maximum of 72 characters.

   For information about activating bcrypt password hashing,
   see :ref:`password-management-hashes-bcrypt`.

   :Default value: false
   :Possible values: ``true``, ``false``
   :Type: boolean


.. envvar:: password/hashing/bcrypt/cost_factor

   Sets the bcrypt cost factor,
   which increases password security by slowing down the hashing computation.
   Higher values require more time to hash a password,
   making brute-force attacks more expensive.
   However, higher values also slow down legitimate password changes and authentication.

   The cost factor must be an integer between 4 and 31.
   Each increment approximately doubles the hashing time.

   This setting only affects newly created or changed user passwords.
   Existing bcrypt hashes with a different cost factor remain unchanged.

   For information about configuring bcrypt settings,
   see :ref:`password-management-hashes-bcrypt-settings`.

   :Default value: ``12``
   :Possible values: Integer between ``4`` and ``31``
   :Type: positive integer


.. envvar:: password/hashing/bcrypt/prefix

   Specifies the bcrypt variant identifier to use when hashing passwords.
   Different bcrypt variants have different properties and compatibility levels.

   The recommended value is ``2b``, which is the patched bcrypt variant
   and the current standard for most systems.
   The value ``2a`` represents the original bcrypt variant and isn't recommended.
   The values ``2x`` and ``2y`` are legacy variants, and you rarely use them.

   This setting only affects newly created or changed user passwords.
   Existing bcrypt hashes with a different prefix remain unchanged.

   For information about configuring bcrypt settings,
   see :ref:`password-management-hashes-bcrypt-settings`.

   :Default value: ``2b``
   :Possible values: ``2a``, ``2b``, ``2x``, ``2y``
   :Type: string


.. envvar:: password/hashing/method

   Specifies the password hashing algorithm to use when storing user passwords in the directory service.
   You can choose between MD5, SHA-256, or SHA-512.
   Each algorithm offers a different balance between compatibility and security.

   MD5
      Deprecated and less secure than the SHA algorithms.
      Do not use MD5 for new installations.

   SHA-256
      More secure than MD5.
      Suitable for most deployments.

   SHA-512
      More secure than SHA-256.
      Recommended for new installations and systems with high-security requirements.

   The hashing algorithm only affects newly created or changed user passwords.
   Existing passwords keep their original hashing algorithm.

   To use bcrypt as the hashing method instead,
   see :envvar:`password/hashing/bcrypt`.

   For information about password hashing,
   see :ref:`password-management-hashes`.

   :Default value: ``SHA-512``
   :Possible values: ``MD5``, ``SHA-256``, ``SHA-512`` (case-insensitive)
   :Type: string


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


.. envvar:: portal/default-dn

   Specifies the LDAP distinguished name of the portal object
   that holds the configuration for the *Portal*.
   After you change this variable,
   run :command:`univention-portal update` to apply the change.

   :Default value: :samp:`cn=domain,cn=portal,cn=portals,cn=univention,{ldap/base}`
   :Type: string


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


.. envvar:: ssl/validity/host

   Stores the expiry date of the local host certificate.
   A daily cron job on each Nubus for UCS system updates this value
   after checking the host certificate.
   The value is the number of days elapsed since 1970-01-01.

   .. note::

      Nubus for UCS sets this variable automatically.
      Don't change it manually.

   For information about monitoring certificate expiry,
   see :ref:`domain-infrastructure-tls-monitoring`.

   :Default value: not set
   :Type: integer (days since 1970-01-01)


.. envvar:: ssl/validity/root

   Stores the expiry date of the root certificate.
   A daily cron job on each Nubus for UCS system updates this value
   after checking the root certificate.
   The value is the number of days elapsed since 1970-01-01.

   .. note::

      Nubus for UCS sets this variable automatically.
      Don't change it manually.

   For information about monitoring certificate expiry,
   see :ref:`domain-infrastructure-tls-monitoring`.

   :Default value: not set
   :Type: integer (days since 1970-01-01)


.. envvar:: ssl/validity/warning

   Sets the warning threshold in days for root certificate expiry.
   When the root certificate expires within the configured number of days,
   the *Management UI* displays a warning.
   The Nagios plugin also uses this threshold for its certificate validity check.

   For information about monitoring certificate expiry,
   see :ref:`domain-infrastructure-tls-monitoring`.

   :Default value: ``30``
   :Type: integer


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

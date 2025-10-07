.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _profile-intro:

**************************
Profile-based installation
**************************

In addition to the interactive installation described in the
:cite:t:`ucs-manual`, a profile-based installation of UCS is also possible. With
this method, the settings for the Debian Installer and |UCSUSS| are specified in a
preseed file.

The Debian Installer consists of a number of special-purpose components to
perform each installation task. Each component performs its task, asking the
user questions as necessary to do its job. The questions themselves are given
priorities, and the priority of questions to be asked is set when the installer
is started.

When a default installation is performed, only essential (``priority=high``)
questions will be asked. This results in a highly automated installation process
with little user interaction.

If there is a problem, the user will see an error screen, and the installer menu
may be shown in order to select some alternative action. Serious error
notifications are set to ``priority=critical`` so the user will always be
notified.

Power users may be more comfortable with a menu-driven interface, where each
step is controlled by the user rather than the installer performing each step
automatically in sequence. To use the installer in a manual, menu-driven way,
add the boot argument ``priority=medium``.

If your hardware requires you to pass options to kernel modules as they are
installed, you will need to start the installer in “expert” mode. This can be
done by adding the boot argument ``priority=low``.

Depending on the selected priority the installer will ask more or less
questions. The installer will either use internal default values or the values
from the profile. To perform the installation fully unattended all required
answers must be provided through the installation profile. Therefore
``priority=critical`` should be specified under *additional start
options* for UCS systems using the profile from :ref:`example`.

.. _structure:

Structure of profile files
==========================

An installation profile is a text file which can be edited with any editor. The
file must use the UTF-8 character encoding. Empty lines and lines starting with
a hash character (``#``) are ignored. All other lines should follow the four
column layout required by :program:`debconf`, which is fully described in
:cite:t:`debian-preseed`:

::

   # Comment
   <owner> <question name> <question type> <value>


The owner of most questions will be ``d-i``, which is the *Debian Installer*.
The *question type* depends on the questions and can be ``boolean``, ``string``
or ``select``. Any questions not answered by the preseed file is asked
interactively and will prevent an unattended installation.

.. _example:

Example installation profile
============================

A template file is provided as
:file:`/usr/share/doc/univention-net-installer/examples/TEMPLATE`.

.. note::

   The file may be stored compressed with the :file:`.gz` extension. Use
   :command:`gunzip` to extract a copy of that file.

It contains the minimum required settings to perform a fully automatic
installation of a |UCSMANAGEDNODE| with no additional software. It will use the
German keyboard layout and language settings. It will re-partition the hard-disk
without asking any questions and will use LVM to manage the disk space. No
additional software will be installed.

.. code-block::
   :linenos:
   :emphasize-lines: 8,33,55,66,70,123

   #
   # This file overwrites /proc/cmdline overwrites preseed.cfg in the InitRamFs!
   #

   #
   # The following options must be set through the PXE configuration
   #
   # Delay asking for locale and keyboard layout after preseeding via network
   #d-i auto-install/enable boolean true
   # Only ask for critical questions
   #d-i debconf/priority select critical
   # Disable graphical installer
   #d-i debian-installer/framebuffer boolean false

   # no live installer
   d-i live-installer/enable boolean false

   #
   # Use interfaces with link
   #
   d-i netcfg/dhcp_timeout string 60

   #
   # Use dummy hostname and domain
   #
   d-i netcfg/get_hostname string unassigned-hostname
   d-i netcfg/get_domain string unassigned-domain
   krb5-config krb5-config/default_realm string UNASSIGNED-REALM
   krb5-config krb5-config/kerberos_servers string localhost
   krb5-config krb5-config/admin_server string localhost

   #
   # Select German as default locale and for keyboard layout
   #
   d-i debian-installer/locale string de_DE.UTF-8
   d-i keyboard-configuration/xkb-keymap select de(nodeadkeys)
   #d-i keyboard-configuration/modelcode string pc105
   d-i ucr/xorg/keyboard/options/XkbModel string pc105
   #d-i keyboard-configuration/layoutcode string de
   d-i ucr/xorg/keyboard/options/XkbLayout string de
   #d-i keyboard-configuration/variantcode string nodeadkeys
   d-i ucr/xorg/keyboard/options/XkbVariant string nodeadkeys
   #d-i keyboard-configuration/optionscode string
   d-i ucr/xorg/keyboard/options/XkbOptions string
   #d-i debian-installer/keymap select de-latin1-nodeadkeys

   #
   # Configure local repository server
   #
   d-i debian-installer/allow_unauthenticated boolean true
   d-i mirror/country string manual
   d-i mirror/protocol select http
   d-i mirror/http/proxy string
   # The host name of the repository server is filled through the PXE configuration generated by UDM
   #d-i mirror/http/hostname string updates.software-univention.de
   d-i mirror/http/directory string /univention-repository/
   d-i mirror/codename string ucs507
   d-i mirror/suite string uc507
   d-i mirror/udeb/suite string ucs507

   #
   # Disable password for user 'root'
   #
   d-i passwd/root-login boolean true
   # Alternative: printf "secret" | mkpasswd -s -m sha-512
   d-i passwd/root-password-crypted string *
   d-i passwd/make-user boolean false

   #
   # Partition hard disk: Use "lvm" and one big "/" partition
   #
   # Choices: lvm crypto regular
   d-i partman-auto/method string lvm
   # Choices: atomic home multi
   d-i partman-auto/choose_recipe string atomic
   d-i partman-auto/init_automatically_partition select 60some_device_lvm
   d-i partman-auto/init_automatically_partition seen false
   d-i partman-auto-lvm/new_vg_name string vg_ucs
   d-i partman-lvm/device_remove_lvm boolean true
   d-i partman-md/device_remove_md boolean true
   d-i partman-lvm/confirm boolean true
   d-i partman-lvm/confirm_nooverwrite boolean true
   d-i partman-partitioning/confirm_write_new_label boolean true
   d-i partman/choose_partition select finish
   d-i partman/confirm boolean true
   d-i partman/confirm_nooverwrite boolean true

   # Pre-select the standard UCS kernel
   #d-i base-installer/kernel/image string linux-image-amd64
   d-i base-installer/includes string less univention-config
   d-i base-installer/debootstrap_script string /usr/share/debootstrap/scripts/sid

   #
   # Only minimal install
   #
   d-i apt-setup/use_mirror boolean false
   d-i apt-setup/no_mirror boolean true
   d-i apt-setup/services-select multiselect none
   d-i apt-setup/cdrom/set-first boolean false
   tasksel tasksel/first multiselect none
   d-i pkgsel/include string univention-system-setup-boot univention-management-console-web-server univention-management-console-module-setup linux-image-amd64 openssh-server univention-base-packages
   postfix postfix/main_mailer_type string No configuration
   openssh-server ssh/disable_cr_auth boolean false
   d-i ucf/changeprompt select keep_current
   d-i pkgsel/upgrade select none
   popularity-contest popularity-contest/participate boolean false

   #
   # Install GRUB in MBR by default on new systems
   #
   d-i grub-installer/only_debian boolean true
   d-i grub-installer/bootdev string default
   grub-pc grub-pc/install_devices multiselect
   grub-pc grub-pc/install_devices_empty boolean true

   #
   # After installation
   #
   d-i finish-install/reboot_in_progress note
   d-i cdrom-detect/eject boolean true

   #
   # Disable starting "Univention System Setup Boot"
   #
   d-i ucr/system/setup/boot/start string false

   #
   # Univention System Setup profile
   #
   #univention-system-setup-boot uss/root_password string
   univention-system-setup-boot uss/components string
   univention-system-setup-boot uss/packages_install string
   univention-system-setup-boot uss/packages_remove string
   # Choices: domaincontroller_master domaincontroller_backup domaincontroller_slave memberserver
   univention-system-setup-boot uss/server/role string memberserver
   #univention-system-setup-boot uss/ldap/base string dc=example,dc=com

.. _preseed-pxe:

.. rubric:: Explain example

#. Line 8: These settings must be configured as PXE command line parameters in
   :guilabel:`additional start options`. They are listed here for reference only
   and cannot be changed through this file:

   * The parameter ``auto-install/enable`` is used to switch the order of some
     installer modules: The network should be configured and the
     :file:`preseed.cfg` should be loaded *before* the first questions about the
     locale settings are asked.

   * The parameter ``netcfg/choose_interface=auto`` tells the installer to use
     the same interface which was used for the PXE boot.

   * Also some of those early questions are asked at priority level ``high``.
     The priority level should be raised to ``critical`` to hide them.

   The long parameter names can be abbreviated as ``auto=true priority=critical
   interface=auto``.

#. Line 33: If the locale settings are not consistent, the installer will ask
   interactively for corrections. The keyboard related settings must be
   configured through |UCSUCR| - the questions starting with
   ``keyboard-configuration/xkb-…`` will not work!

#. Line 55: The location of the local repository is filled in through the PXE
   configuration. By default the value of the |UCSUCRV|
   :envvar:`repository/online/server` is used. It can be over-written by
   specifying the value here in the profile file. For use with the public
   repository specify ``updates.software-univention.de`` here.

#. Line 66: By default no password is set, which will prevent logging in. It should be
   replaced by an encrypted password, which can be used by running a command
   like :command:`printf "secret" \| mkpasswd -s -m sha-512`

#. Line 70: By default all existing partitions will be wiped without asking any question!
   They will be replaced by a single file system for :file:`/` using LVM. See
   :cite:t:`debian-preseed` for more advanced partitioning schemas.

#. Line 123: This section contains the UCS specific settings, which are normally
   configured through |UCSUSS|. For an unattended installation the graphical
   installer is disabled. All other values starting with ``uss/`` are copied to
   the installation profile. The variables are described in
   :ref:`variables`.

.. _variables:

Overview of profile variables
=============================

.. _variables-system:

Profile variables - System properties
-------------------------------------

The following profile variables can be used to specify basic properties
of the computer such as the computer name, its role within the UCS
domain and the name of the domain the computer should join.

.. list-table:: Profile variables - System properties
   :header-rows: 1
   :widths: 3 9

   * - Name
     - Function

   * - :envvar:`server/role`
     - The system role. You may choose from ``domaincontroller_master`` (for
       |UCSPRIMARYDN|), ``domaincontroller_backup`` (for |UCSBACKUPDN|),
       ``domaincontroller_slave`` (for |UCSREPLICADN|) and ``memberserver`` (for
       |UCSMANAGEDNODE|). The properties of the system roles are described in
       the domain services chapter of the :cite:t:`ucs-manual`.

   * - :envvar:`hostname`
     - The computer name. The name must only contain the letters ``a`` to ``z``
       in lowercase, the figures ``0`` to ``9`` and hyphens. Although underscore
       are allowed as well, they should not be used as they are not supported
       everywhere. The name must begin with a letter.

   * - :envvar:`domainname`
     - The name of the DNS domain in which the computer is joined.

   * - :envvar:`windows/domain`
     - The name of the NetBIOS domain used by Samba. This variable should only
       by defined for the system role |UCSPRIMARYDN|.

   * - ``locales``
     - Localization packages to be installed (locales). If more than one locale
       is specified, the locales are separated by blank spaces.

   * - :envvar:`locale/default`
     - The standard locale for the computer, e.g. ``en_GB.UTF-8:UTF-8``. More
       information on system locales can be found at :cite:t:`locales`.

   * - ``country``, ``keymap``
     - The keyboard layout for the computer, specified in the form of an X11
       key map entry, e.g. ``de-latin1``.

   * - ``timezone``
     - The time zone for the computer, e.g. ``Europe/Berlin``. A complete list
       of possible configuration options is shown in the *Basic settings* module
       of the Univention Management Console.

   * - ``root_password``
     - The password for the ``root`` user for this computer. On a |UCSPRIMARYDN|,
       this password is also used for the ``Administrator`` password.

.. _variables-join:

Profile variables - LDAP settings and domain joins
--------------------------------------------------

Automatically joining the computer into the domain is currently not
supported for security reasons.

.. list-table:: Profile variables - LDAP settings and domain joins
   :header-rows: 1
   :widths: 3 9

   * - Name
     - Function

   * - ``start/join``
     - As standard, all computers apart from the |UCSPRIMARYDN| attempt to join
       the UCS domain in the course of the installation. If this parameter is
       set to ``false``, the automatic domain join is deactivated.

   * - :envvar:`ldap/base`
     - The base DN of the LDAP domain. In general, the base DN
       ``dc=example,dc=com`` is used in a domain ``example.com``. This variable
       is only evaluated on the system role |UCSPRIMARYDN|.

.. _variables-network:

Profile variables - Network configuration
-----------------------------------------

By default automatically installed systems use DHCP. The following profile
variables can be used to specify the network configuration of the computer.

General information on the network configuration and the use of the name servers
can be found in Chapter *Network configuration* of the :cite:t:`ucs-manual`.

The settings for network cards must be performed completely. It is not possible
to leave individual settings blank. For example, if there is no IP address for
the device ``eth0`` in the profile, in addition to the IP address, the
:envvar:`interfaces/eth0/netmask` will also be requested.

.. list-table:: Profile variables - Network configuration
   :header-rows: 1
   :widths: 5 7

   * - Name
     - Function

   * - :samp:`interfaces/eth{N}/type`
     - If this parameter is set to ``dynamic`` or ``dhcp``, the network
       interface :samp:`eth{N}` procures its network configuration via DHCP. The
       settings of :samp:`interfaces/eth{N}/address`,
       :samp:`interfaces/eth{N}/netmask`, :samp:`interfaces/eth{N}/network`,
       :samp:`interfaces/eth{N}/broadcast`, :samp:`nameserver{N}` and
       ``gateway`` then become optional, but can still be used to over-write the
       configuration provided by DHCP.

       If no DHCP offer is received, a random IP address from the link-local
       network :samp:`169.25 4.{x.x}` is used.

       For manual configuration this parameter must be set to ``static``.

   * - :samp:`interfaces/eth{N}/address`
     - The IPv4 address of the physical network interface :samp:`eth{N}`.

   * - :samp:`interfaces/eth{N}/netmask`
     - The network mask of the subnetwork from which the IPv4 address of
       :samp:`eth{N}` originates.

   * - ``gateway``
     - The IPv4 address of the gateway which the computer should use as
       standard. Alternatively, one can specify the computer name or the FQDN
       that can be resolved into the IP address.

   * - :samp:`interfaces/eth{N}/ipv6/{name}/address`
     - An IPv6 address of the physical network interface :samp:`eth{N}` in
       static configuration. Multiple addresses can be assigned by using
       different :samp:`name` prefixes.

   * - :samp:`interfaces/eth{N}/ipv6/{name}/prefix`
     - The prefix length of the IPv6 address of the physical network interface
       :samp:`eth{N}` in static configuration.

   * - ``ipv6/gateway``
     - The IPv6 address of the gateway which the computer should use as
       standard. It is not obligatory to enter a gateway for IPv6, but
       recommended. An IPv6 gateway configured here has preference over router
       advertisements, which might otherwise be able to change the route.

   * - :samp:`interfaces/eth{N}/acceptRA`
     - If this setting is set to ``yes``, the stateless address
       auto-configuration (SLAAC) is used. In this case, the IP address is
       assigned from the routers of the local network segment. If the variable
       is set to ``no``, the configuration is performed statically via
       :samp:`interfaces/eth{N}/ip6` and :samp:`interfaces/eth{N}/prefix6` (see
       there).

   * - :envvar:`nameserver1`,
       :envvar:`nameserver2`,
       :envvar:`nameserver3`
     - The IP address of the name server which should perform the name
       resolution. It is possible to specify up to three name servers.

   * - :envvar:`dns/forwarder1`,
       :envvar:`dns/forwarder2`,
       :envvar:`dns/forwarder3`
     - The IP address of the name server intended to serve as the forwarder for
       a locally installed DNS service. It is possible to specify up to three
       forwarders.

   * - :envvar:`proxy/http`
     - The URL of a proxy server to be used when accessing the internet. The
       specified URL is adopted in the |UCSUCR| variables :envvar:`proxy/http`
       and :envvar:`proxy/ftp`. This setting is only required if packages are to
       be installed which download additional packages from external web
       servers; e.g., the installation program for the Flash plugin. Example:
       :samp:`proxy/http="http://proxy.example.com:8080"`

.. _variables-software:

Profile variables - Software selection
--------------------------------------

The following profile variables refer to software packages which are to
be installed on the computer.

.. list-table:: Profile variables - Software selection
   :header-rows: 1
   :widths: 3 9

   * - Name
     - Function

   * - ``packages_install``
     - This settings names packages which are additionally installed. If more
       than one package is specified, the packages are separated by blank
       spaces.

   * - ``packages_remove``
     - This settings names packages which should be removed. If more than one
       package is specified, the packages are separated by blank spaces.

.. _variables-ssl:

Profile variables - SSL
-----------------------

A SSL certification infrastructure is set up during installation of a
|UCSPRIMARYDN|. If no settings are configured, automatic names are given
for the certificate.

.. list-table:: Profile variables - SSL
   :header-rows: 1
   :widths: 4 8

   * - Name
     - Function

   * - :envvar:`ssl/country`
     - The ISO country code of the certification body appearing in the
       certificate (root CA), specified with two capital letters.

   * - :envvar:`ssl/state`
     - The region, county or province that appears in the certificate of the
       root CA.

   * - :envvar:`ssl/locality`
     - Place appearing in the certificate of the root CA.

   * - :envvar:`ssl/organization`
     - Name of the organization that appears in the certificate of the root CA.

   * - :envvar:`ssl/organizationalunit`
     - Name of the organizational unit or department of the organization that
       appears in the certificate of the root CA.

   * - :envvar:`ssl/email`
     - Email address that appears in the certificate of the root CA.

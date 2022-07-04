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
options* for UCS systems using the profile from :ref:`profile-example`.

.. _profile-structure:

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

.. _profile-example:

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
   d-i mirror/codename string ucs502
   d-i mirror/suite string uc502
   d-i mirror/udeb/suite string ucs502

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
   :ref:`profile-variables`.

.. _profile-variables:

Overview of profile variables
=============================

.. _profile-variables-system:

Profile variables - System properties
-------------------------------------

The following profile variables can be used to specify basic properties
of the computer such as the computer name, its role within the UCS
domain and the name of the domain the computer should join.

.. list-table:: Profile variables - System properties
   :header-rows: 1

   * - Name
     - Function

   * - ``server/role``
     - The system role. You may choose from ``domaincontroller_master`` (for
       |UCSPRIMARYDN|), ``domaincontroller_backup`` (for |UCSBACKUPDN|),
       ``domaincontroller_slave`` (for |UCSREPLICADN|) and ``memberserver`` (for
       |UCSMANAGEDNODE|). The properties of the system roles are described in
       the domain services chapter of the :cite:t:`ucs-manual`.

   * - ``hostname``
     - The computer name. The name must only contain the letters ``a`` to ``z``
       in lowercase, the figures ``0`` to ``9`` and hyphens. Although underscore
       are allowed as well, they should not be used as they are not supported
       everywhere. The name must begin with a letter.

   * - ``domainname``
     - The name of the DNS domain in which the computer is joined.

   * - ``windows/domain``
     - The name of the NetBIOS domain used by Samba. This variable should only
       by defined for the system role |UCSPRIMARYDN|.

   * - ``locales``
     - Localization packages to be installed (locales). If more than one locale
       is specified, the locales are separated by blank spaces.

   * - ``locale/default``
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

.. _profile-variables-join:

Profile variables - LDAP settings and domain joins
--------------------------------------------------

Automatically joining the computer into the domain is currently not
supported for security reasons.

.. list-table:: Profile variables - LDAP settings and domain joins
   :header-rows: 1

   * - Name
     - Function

   * - ``start/join``
     - As standard, all computers apart from the |UCSPRIMARYDN| attempt to join
       the UCS domain in the course of the installation. If this parameter is
       set to ``false``, the automatic domain join is deactivated.

   * - ``ldap/base``
     - The base DN of the LDAP domain. In general, the base DN
       ``dc=example,dc=com`` is used in a domain ``example.com``. This variable
       is only evaluated on the system role |UCSPRIMARYDN|.

.. _profile-variables-network:

Profile variables - Network configuration
-----------------------------------------

By default automatically installed systems use DHCP. The following profile
variables can be used to specify the network configuration of the computer.

General information on the network configuration and the use of the name servers
can be found in Chapter *Network configuration* of the :cite:t:`ucs-manual`.

The settings for network cards must be performed completely. It is not possible
to leave individual settings blank. For example, if there is no IP address for
the device ``eth0`` in the profile, in addition to the IP address, the
``interfaces/eth0/netmask`` will also be requested.

.. list-table:: Profile variables - Network configuration
   :header-rows: 1

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

   * - ``nameserver1``,
       ``nameserver2``,
       ``nameserver3``
     - The IP address of the name server which should perform the name
       resolution. It is possible to specify up to three name servers.

   * - ``dns/forwarder1``,
       ``dns/forwarder2``,
       ``dns/forwarder3``
     - The IP address of the name server intended to serve as the forwarder for
       a locally installed DNS service. It is possible to specify up to three
       forwarders.

   * - ``proxy/http``
     - The URL of a proxy server to be used when accessing the internet. The
       specified URL is adopted in the |UCSUCR| variables :envvar:`proxy/http`
       and :envvar:`proxy/ftp`. This setting is only required if packages are to
       be installed which download additional packages from external web
       servers; e.g., the installation program for the Flash plugin. Example:
       ``proxy/http="http://proxy.example.com:8080"``

.. _profile-variables-software:

Profile variables - Software selection
--------------------------------------

The following profile variables refer to software packages which are to
be installed on the computer.

.. list-table:: Profile variables - Software selection
   :header-rows: 1

   * - Name
     - Function

   * - ``packages_install``
     - This settings names packages which are additionally installed. If more
       than one package is specified, the packages are separated by blank
       spaces.

   * - ``packages_remove``
     - This settings names packages which should be removed. If more than one
       package is specified, the packages are separated by blank spaces.

.. _profile-variables-ssl:

Profile variables - SSL
-----------------------

A SSL certification infrastructure is set up during installation of a
|UCSPRIMARYDN|. If no settings are configured, automatic names are given
for the certificate.

.. list-table:: Profile variables - SSL
   :header-rows: 1

   * - Name
     - Function

   * - ``ssl/country``
     - The ISO country code of the certification body appearing in the
       certificate (root CA), specified with two capital letters.

   * - ``ssl/state``
     - The region, county or province that appears in the certificate of the
       root CA.

   * - ``ssl/locality``
     - Place appearing in the certificate of the root CA.

   * - ``ssl/organization``
     - Name of the organization that appears in the certificate of the root CA.

   * - ``ssl/organizationalunit``
     - Name of the organizational unit or department of the organization that
       appears in the certificate of the root CA.

   * - ``ssl/email``
     - Email address that appears in the certificate of the root CA.

.. _profile-netinstaller:

Network-based PXE installations with Univention Net Installer
=============================================================

Network-based, profile-based installations via PXE are performed with the
Univention Net Installer, which can be set up using the package
:program:`univention-net-installer`. This installs the required TFTP server and
WWW server configuration. In addition a DHCP server is required, which is
provided by the package :program:`univention-dhcp`. If the DHCP server and the
PXE server of the Univention Net Installer are operated on separate systems, the
PXE server must be assigned via a DHCP boot policy.

.. code-block:: console

   $ univention-install univention-net-installer univention-dhcp


The installation process consists of multiple steps, which contact different
services and servers:

1. First the *DHCP server* is contacted. It sends the client to the
   *Boot server* (by default the DHCP server itself) configured
   through the *DHCP Boot* policy to request the boot loader given in
   *Boot filename* (:file:`pxelinux.0`).

2. Then the client downloads the boot loader via the ``TFTP`` protocol from the
   *PXE server*. The boot loader scans the server for the client configuration
   file in :file:`pxelinux.cfg/`. The referenced Linux kernel (:file:`linux`)
   and initial RAM disk file (:file:`initrd.gz`) are then downloaded. Those
   names can be changed through the |UCSUCRV|\ s :envvar:`pxe/installer/kernel`
   and :envvar:`pxe/installer/initrd`.

   .. note::

      Newer versions of the PXE boot loader support downloading through
      ``http``, which can be faster and more reliable in certain environments.
      This can be enabled by specifying URLs starting with ``http://`` as file
      names.

3. Finally the UCS installer downloads the profiles and package files using
   ``http``. The *Name of the installation profile* is configured in
   the computer entry in LDAP. The file is fetched from the *PXE server* by
   default, but the prefix can be overwritten through the |UCSUCRV|
   :envvar:`pxe/installer/profiles`. As an alternative the name can also be
   specified as an absolute URL.

4. The package files are fetched from the *repository server*, which is
   configured through the |UCSUCRV| :envvar:`repository/online/server` on the
   PXE server.

Univention Net Installer supports both the interactive and profile-based
installation. Any questions not answered in the preseed file forces the
installer to interactive mode.

Profiles should be copied into the directory :file:`/var/lib/univention-client-boot/preseed/` on
the PXE server, which is accessible through
:samp:`http://{HOST-NAME}/univention-client-boot/preseed/`.

Univention Net Installer can either directly use the repository server
https://updates.software-univention.de/ or a local repository
server. The later one is advisable as it reduces the amount of data
needing to be downloaded for each installation.

.. _profile-netinstaller-local:

Local repository
----------------

The local repository must first be initialized once using the command
:command:`univention-repository-create`. Since UCS 5.0-0 the
PXE kernel and installer must be copied manually from the ISO image to
the correct location in :file:`/var/lib/univention-client-boot/installer/`.

.. code-block:: console

   $ mount /dev/cdrom /media/cdrom0
   $ install -m644 /media/cdrom0/netboot/linux \
   > /var/lib/univention-client-boot/
   $ install -m644 /media/cdrom0/netboot/initrd.gz \
   > /var/lib/univention-client-boot/
   $ umount /media/cdrom0


Instead of mounting the DVD a downloaded ISO image can also be mounted by using
:command:`mount -o loop,ro /path/to/UCS.iso /media/cdrom0`. Alternatively the
files can be downloaded from
`<http://updates.software-univention.de/pxe/5.0-2/amd64/gtk/debian-installer/amd64/>`_:

.. code-block:: console

   $ cd /var/lib/univention-client-boot/
   $ PXE='http://updates.software-univention.de/pxe/'
   $ PXE+=$(ucr filter <<<'@%@version/version@%@-@%@version/patchlevel@%@')
   $ PXE+=/amd64/gtk/debian-installer/amd64
   $ wget -O linux "$PXE/linux"
   $ wget -O initrd.gz "$PXE/initrd.gz"


The procedure should be repeated for each new release. Otherwise new
installations will still start with an older release, which might require extra
time for updating. For more information on local repositories, see the software
deployment chapter of the :cite:t:`ucs-manual`.

.. _profile-netinstaller-public:

Public repository
-----------------

Even when the public repository server
`<https://updates.software-univention.de/>`_ is used, some services and files
must be available inside the local network. At minimum this includes the
``DHCP`` service, which assigns the client its IP address and tells it to
continue fetching files from the next server. Historically this had to be a
``TFTP`` server, but nowadays this also can be any ``HTTP`` server. This has the
benefit that ``HTTP`` is faster, more reliable and also works over the internet.

Install the ``HTTP`` capable boot loader :file:`lpxelinux.0`

.. code-block:: console

   $ ln -s /usr/lib/PXELINUX/lpxelinux.0 \
   > /var/lib/univention-client-boot/


Setup the *DHCP Boot* policy to use :file:`lpxelinux.0`. Depending on the
capabilities of the network card boot code the boot loader can either be fetched
over the ``HTTP`` or ``TFTP`` protocol:

For ``HTTP`` configure the absolute URL as the ``boot filename``:

.. code-block:: console

   $ HOST="$(hostname -f)"
   $ LDAP="$(ucr get ldap/base)"
   $ HTTP="http://$HOST/univention-client-boot/lpxelinux.0"
   $ udm policies/dhcp_boot modify \
   > --dn "cn=default-settings,cn=boot,cn=dhcp,cn=policies,$LDAP" \
   > --set boot_filename="$HTTP" \
   > --set boot_server=


The installer performs its own second DHCP request. This again retrieves the
DHCP option ``boot filename``, which now contains the *URL* to the PXE loader.
The installer wrongly interprets this as the URL for the profile
:file:`preseed`, which breaks the installation. Therefore the option needs to be
overwritten when the installer performs this second query:

.. code-block:: console

   $ STMT='if substring (option vendor-class-identifier, 0, 3) = "d-i" { filename ""; }'
   $ udm dhcp/subnet list |
   > sed -ne 's/^DN: //p' |
   >   xargs -d '\n' -n1 udm dhcp/subnet modify \
   >     --option options \
   >     --append statements="$STMT" \
   >     --dn


For ``TFTP`` change ``boot filename`` to point to :file:`lpxelinux.0`:

.. code-block:: console

   $ HOST="$(hostname -f)"
   $ LDAP="$(ucr get ldap/base)"
   $ udm policies/dhcp_boot modify \
   > --dn "cn=default-settings,cn=boot,cn=dhcp,cn=policies,$LDAP" \
   > --set boot_filename='lpxelinux.0' \
   > --set boot_server="$HOST"


Configure the boot loader to load the Linux kernel and initial ram disk from the
public repository server:

.. code-block:: console

   $ PXE='http://updates.software-univention.de/pxe'
   $ PXE="$PXE/5.0-2/amd64/gtk/debian-installer/amd64"
   $ ucr set \
   > pxe/installer/kernel="$PXE/linux" \
   > pxe/installer/initrd="$PXE/initrd.gz" \
   > pxe/installer/ipappend=3


In the profile file the settings for ``mirror/http/hostname`` and
``mirror/http/directory`` must be changed to use the public server and its
layout:

::

   d-i mirror/http/hostname string updates.software-univention.de
   d-i mirror/http/directory string /


.. _profile-assign:

Assignment of a computer for automatic installation
---------------------------------------------------

A computer to be installed via Univention Net Installer must firstly be
registered in the computer management of the |UCSUMC|. The following values must
be set as a minimum at the *General* tab:

* Hostname

* MAC address

* IP address

* DNS forward and reverse zone entries

* DHCP service entry

The :guilabel:`(Re-)install on next boot` option must now be activated in the
*Advanced settings* tab under *Deployment*.

The name of the installation profile relative to
:file:`/var/lib/univention-client-boot/preseed/` can be entered under
:guilabel:`Name of installation profile`. As an alternative any other ``http``
server can be used as well, in which case an absolute URL must be given.

Options entered under *additional start options* are passed on to the
kernel in network-based installations, e.g., for the deactivation of ACPI during
system start. This can also be used to specify other preseed variables on a
host-by-host basis. To perform an installation fully unattended see the
:ref:`preseed-pxe` for a list of required options.

A PXE configuration file is created for every computer object under
:file:`/var/lib/univention-client-boot/pxelinux.cfg/`.

.. tip::

   Several |UCSUCRV| exist on the PXE server, which can be used to further
   customize the PXE configuration. Use :command:`ucr search ^pxe/` to get a
   list of them including a short description. Those values will only be used
   when next a PXE configuration file is generated.

It must be verified that the boot order in BIOS of the system to be installed
prefers a PXE network boot over hard disks or CD-ROMs.

On the next restart of the computer it will boot via PXE and is installed via
the network.

By default the *(Re-)install on next boot* option needs to be reset manually
after the installation has finished. Otherwise the computer will be reinstalled
every time the host is booted! If the package
:program:`univention-net-installer-daemon` is installed on the server, the flag
can be reset automatically.

.. spelling::

   preseed

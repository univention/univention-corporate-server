.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-installation-physical:

Physical and virtual machine installation
=========================================

The following sections describe how to install Nubus for Univention Corporate Server (UCS).
You install Nubus for UCS from DVD on physical hardware,
or from DVD image for virtual machines.
The installation is interactive
and prompts all the necessary system settings in a graphic interface.

The installation DVD is available for the computer architecture ``amd64``, 64-bit.
In addition to support for the widely distributed BIOS systems,
the DVD also includes support for the Unified Extensible Firmware Interface (UEFI) standard.
The UEFI support on the DVD is also capable of starting systems with activated Secure Boot
and installing Nubus for UCS there.

.. important::

   Univention doesn't support the simultaneous operation of UCS and Debian on a UEFI system.

   The reason for this is the GRUB boot loader of Nubus for UCS
   that partly uses the same configuration files as Debian.

   An already installed Debian leads to the fact
   that the hardware can't boot Nubus for UCS anymore
   after the installation of or an update to UCS 5.2.
   A subsequent installation of Debian also results in Nubus for UCS 5.2 not being able to boot.

Besides operating Nubus for UCS on hardware or in a virtualization solution,
you can also install it on the Amazon EC2 cloud using an AMI image.
For more information,
see :ref:`installation-amazon-ec2`.

You can use the installation interfaces with a keyboard and with mouse.

* Use the :kbd:`Tab` key to jump to the next field.

* Use the :kbd:`Shift+Tab` keys to jump back to the previous field.

* Use the :kbd:`Enter` key to assign values to the input field and confirm buttons.

* Use the arrow keys inside a list or table for navigating between entries.

.. note::

   Use :guilabel:`Cancel` to cancel the current configuration step.
   You can select a previous configuration step again in the menu
   that the installer shows subsequently.
   Under certain circumstances,
   you can't directly select subsequent configuration steps
   if you haven't completed previous steps.

.. _deployment-installation-physical-install-mode:

Select the installation mode
----------------------------

After booting the system from the installation medium,
the screen shows the boot prompt in
:numref:`installation-select-install-mode-isolinux`.

.. _installation-select-install-mode-isolinux:

.. figure:: /images/installer-isolinux.*
   :alt: Installation boot prompt

   Installation boot prompt

You can choose between the following installation procedures:

Start with default settings
   starts the interactive, graphic installation.
   During the installation,
   the system requests a number of parameters such as the network settings,
   hard drive partitions and domain settings for the UCS system to be installed and then performs the installation and the configuration.

.. _deployment-installation-physical-install-mode-manual-network:

Start with manual network settings
   runs a standard installation
   that doesn't automatically configure the network through DHCP.
   Use this option for system installation,
   where you need to set up the network manually.

Advanced options
   The submenu offers advanced options for the installation process for selection:

   .. _deployment-installation-physical-install-mode-text-mode:

   Start in text mode
      runs an interactive standard installation in text mode.
      Use this option on systems which have problems with the graphic version of the installer.

   Rescue mode
      serves to recover systems that are unable to boot.

   Boot from first hard drive
      boots the operating system installed on the first hard drive
      instead of the Nubus for UCS installation.

Accessible dark contrast installer menu
   allows running the setup in a dark and contrast rich mode
   for visually impaired persons.

After you select one option,
the boot loader runs the kernel from the installation medium.
The installation consists of separate modules
that the installer loads subsequently from the installation medium, if necessary.
For example, the installer has modules for network configuration
or for the selection of software for installation.

.. _deployment-installation-physical-language:

Select the language
-------------------

In the first step, you select the system language that you want to use,
see :numref:`deployment-installation-physical-language-figure`.
The selection has an influence on the use of language-specific characters
and permits the representation of program output in the selected languages
on the installed Nubus for UCS system.

If *Univention Installer* has a translation for the selected language,
it also uses the language during installation.
Otherwise, the installer continues in English.
The installer supports the languages English and German.

.. _deployment-installation-physical-language-figure:

.. figure:: /images/installer-language.*
   :alt: Select the language

   Select the language

.. _deployment-installation-physical-location:

Select the location
-------------------

After the language selection,
the installer shows a list of locations related to the selected language,
see :numref:`deployment-installation-physical-location-figure`.
Select a suitable location from the list.
Nubus for UCS uses the selected location to configure the time zone and the correct language variant.
If the location you want to select isn't in the list,
select ``other`` at the bottom to see an extensive list.

.. _deployment-installation-physical-location-figure:

.. figure:: /images/installer-location.*
   :alt: Select the location

   Select the location

.. _deployment-installation-physical-keyboard-layout:

Select the keyboard layout
--------------------------

You can select the keyboard layout independently of the system language,
see :numref:`deployment-installation-physical-keyboard-layout-figure`.
Select a language compatible with the keyboard.
Otherwise, it may cause operating problems.

.. _deployment-installation-physical-keyboard-layout-figure:

.. figure:: /images/installer-keyboardselection.*
   :alt: Select the keyboard layout

   Select the keyboard layout

.. _deployment-installation-physical-network-configuration:

Set up network configuration
----------------------------

Initially, the Univention Installer attempts to configure the network interfaces automatically,
see :numref:`deployment-installation-physical-network-configuration-dhcp-figure`.
You can deactivate the automatic network interface configuration
by selecting :ref:`deployment-installation-physical-install-mode-manual-network`
from the boot loader menu in
:ref:`deployment-installation-physical-install-mode`.

First, the installer attempts to determine an IPv6 address through the stateless address autoconfiguration (SLAAC).
If unsuccessful, the installer attempts to request an IPv4 address through the Dynamic Host Configuration Protocol (DHCP).
If again successful, the installer skips the manual network configuration.

.. _deployment-installation-physical-network-configuration-dhcp-figure:

.. figure:: /images/installer-netcfg-dhcp.*
   :alt: Automatic network configuration

   Automatic network configuration

If no DHCP server is present in the local network
or your network requires a static configuration of the network interface,
use :guilabel:`Cancel`.
The installer then offers to repeat the automatic configuration
or to configure the interface manually,
see :numref:`deployment-installation-physical-network-configuration-static-figure`.

.. important::

   The installation of Nubus for UCS requires at least one network interface.
   If the installer can't detect a supported network card,
   it opens a list of supported drivers to choose from.

.. _deployment-installation-physical-network-configuration-static-figure:

.. figure:: /images/installer-netcfg-static.*
   :alt: Select the manual network configuration

   Select the manual network configuration

In the manual network configuration you can specify either a static IPv4 or an IPv6 address for the system,
see :numref:`deployment-installation-physical-network-configuration-ip-figure`.
IPv4 addresses have a 32-bit length
and you write them in four blocks in decimal form, for example ``192.0.2.10``.
IPv6 addresses are four times as long and you typically write them in hexadecimal form,
for example ``2001:db8:fe29:de27:0000:0000:0000:0000``.
In addition to a static IP address,
the installer requests values for network mask, gateway, and DNS servers.

.. _deployment-installation-physical-network-configuration-ip-figure:

.. figure:: /images/installer-netcfg-ip.*
   :alt: Specify an IP address

   Specify an IP address

Consider the following points when you specify a DNS server manually.
They depend on the intended subsequent use of the Nubus for UCS system.

* When you install the first Nubus for UCS system and create a Nubus for UCS domain,
  use the IP address of the local router,
  if it provides the DNS service,
  or the DNS server of the internet provider as DNS server address.

* For the installation of every additional Nubus for UCS system,
  use the IP address of a :term:`UCS Primary Directory Node` as the DNS server.
  This is essential for the automatic detection of the UCS Primary Directory Node to work properly.
  In case of doubt, use the IP address of the UCS Primary Directory Node system.

* If the Nubus for UCS system is to join a Windows Active Directory domain during the installation,
  use the IP address of an Active Directory domain controller system as the DNS server.
  This is essential for the automatic detection of the Windows Active Directory domain controller to work properly.

.. _deployment-installation-physical-password:

Define the root password
------------------------

Defining a password for the ``root`` user is necessary to sign in to the installed system,
see :numref:`deployment-installation-physical-password-figure`.
If you install a :term:`UCS Primary Directory Node`
the installer employs this password also the ``Administrator`` domain user.
In later operation, you can manage the passwords for the ``root`` and ``Administrator`` users independent of each other.
You must enter the password twice to ensure it's defined correctly.
For security reasons the password must contain at least eight characters.

.. _deployment-installation-physical-password-figure:

.. figure:: /images/installer-password.*
   :alt: Define the root password

   Define the root password

.. _deployment-installation-physical-partitioning:

Partition the hard drive
~~~~~~~~~~~~~~~~~~~~~~~~

The Univention Installer supports to partition hard drives
and create different file systems, such as ``ext4`` and ``XFS``.
In addition, you can also configure different partition strategies,
such as the logical volume manager (LVM), RAID, or partitions encrypted with LUKS.

The Univention Installer automatically selects a suitable partition model,
MBR or GPT, depending on the size of the selected hard drive.
On systems with the Unified Extensible Firmware Interface (UEFI),
the installer automatically uses the GUID Partition Table (GPT).

The Univention Installer offers guided partitioning to simplify the installation.
In the guided installation,
the installer applies certain standard schemes with respect to the partitioning and formatting to the selected hard drive.
In addition, you can manually partition the hard drive yourself.

The installer offers the following schemes for guided partitioning,
see :numref:`deployment-installation-physical-partitioning-guided-figure`:

Guided - Use entire disk
   The installer creates an individual partition for each file system.
   It doesn't use abstraction layers, such as LVM.
   During the following step, it assigns the number of file systems or partitions.
   The size of the respective hard drive restricts the sizes of the partitions.

.. _deployment-installation-physical-partitioning-lvm:

Guided - Use entire disk and set up LVM
   The installer creates a Logical Volume Group on the selected hard drive first.
   For each file system, it then creates a separate logical volume within the volume group.
   In this scheme, the size of the volume group restricts the size of the logical volume,
   You can subsequently enlarge the size of the volume group with additional hard drives.
   In case of doubt, select this partitioning scheme.

Guided - Use entire disk with encrypted LVM
   This partitioning scheme is the same as :ref:`deployment-installation-physical-partitioning-lvm`,
   with the addition that it uses an encrypted partition for the LVM volume group.
   Consequently, you must enter the password for the encrypted volume group every time you start the system.

.. warning::

   In all mentioned partitioning schemas,
   the installer deletes all existing data on the selected hard drive
   during the partitioning.

.. _deployment-installation-physical-partitioning-guided-figure:

.. figure:: /images/installer-partman-selectguided.*
   :alt: Select the partitioning scheme

   Select the partitioning scheme

Select a hard drive from the list of the detected hard drives,
where you want to apply the partitioning scheme to.

Each partitioning version has the following sub schemas,
which differ in the number of file systems it creates:

All files in one partition
   The installer creates just one partition or logical volume
   for the :file:`/` file system.

Separate :file:`/home` partition
   In addition to a file system for :file:`/`,
   the installer creates an additional file system for :file:`/home/`.

Separate :file:`/home`, :file:`/usr`, :file:`/var` and :file:`/tmp` partition
   In addition to a file system for :file:`/`,
   the installer also creates an additional file system for each of :file:`/home/`, :file:`/usr/`, :file:`/var/`, and :file:`/tmp/`.

Before the installer applies a change to the hard drive,
it summarizes the change again that you must explicitly confirm,
see :numref:`deployment-installation-physical-partitioning-write-lvm-figure`.

.. _deployment-installation-physical-partitioning-write-lvm-figure:

.. figure:: /images/installer-partman-writelvm.*
   :alt: Confirm to apply changes to the hard drive

   Confirm to apply changes to the hard drive

.. _deployment-installation-physical-finish:

Finish installation
~~~~~~~~~~~~~~~~~~~

After the installer completes the partitioning,
it automatically installs the Nubus for UCS base system and additional software.
The software installation takes some time depending on the speed of your hardware.
After software installation,
the installer makes the system ready for boot through installation of the GRUB boot loader,
see :numref:`deployment-installation-physical-finish-reboot-figure`.

.. _deployment-installation-physical-finish-reboot-figure:

.. figure:: /images/installer-reboot.*
   :alt: Finish the installation

   Finish the installation

A restart into the freshly installed system follows subsequently
to complete the system configuration.

.. _deployment-installation-physical-domain-settings:

Set up the domain
~~~~~~~~~~~~~~~~~

You start the final configuration step of the Nubus for UCS system by selecting a domain mode.
The following domain modes are available,
see :numref:`deployment-installation-physical-domain-settings-role-figure`.
They influence the following configuration steps:

.. _deployment-installation-physical-domain-settings-new:

Create a new UCS domain
   The *Create a new UCS domain* configures the first system in a UCS domain,
   a Nubus for UCS system with the :term:`UCS Primary Directory Node` system role.
   The subsequent steps request required information
   to set up the directory service, authentication service, and the DNS server.
   A Nubus for UCS domain can consist of one single or several Nubus for UCS systems.
   You can add additional Nubus for UCS systems at a later point in time
   using the :ref:`deployment-installation-physical-domain-settings-join` mode.
   For more information, see
   :ref:`deployment-installation-physical-domain-settings-new-domain`.

.. _deployment-installation-physical-domain-settings-join-ad:

Join into an existing Active Directory domain
   This mode operates Nubus for UCS as a member of an Active Directory domain.
   The configuration is suitable for expanding an Active Directory domain with applications available on the Nubus platform.
   Apps installed on Nubus for UCS platform are then available for the users of the Active Directory domain to use.
   The subsequent steps request information for joining the Active Directory domain
   and configure Nubus for UCS accordingly.
   For more information, see
   :ref:`deployment-installation-physical-domain-settings-ad-member`.

.. _deployment-installation-physical-domain-settings-join:

Join into an existing UCS domain
   This mode configures the Nubus for UCS system to join an existing Nubus for UCS domain.
   At a later step, the system setup asks for what system role it assigns.
   For more information, see
   :ref:`deployment-installation-physical-domain-settings-join-ucs`.

.. _deployment-installation-physical-domain-settings-role-figure:

.. figure:: /images/installer-domainrole.*
   :alt: Domain settings

   Domain settings

.. _deployment-installation-physical-domain-settings-naming:

Naming convention for hostnames
"""""""""""""""""""""""""""""""

.. index::
   single: hostname; naming convention
   single: hostname
   single: hostname; length
   single: hostname; allowed characters

During Nubus for UCS installation,
the domain setup asks for a hostname and a domain name as *fully qualified domain name*.
For compatibility reasons with Samba and Active Directory domains,
the hostname must adhere to the following naming convention:

* Length from 1 to 13 alphanumeric characters.

* Only lower case letters (``a-z``) and numerals (``0-9``).

* Start and end with an alphanumeric character and can contain a hyphen (``-``) in between.

The naming convention has the following regular expression:

.. code-block::

   ^[a-z0-9][a-z0-9-]{0,11}[a-z0-9]?$

.. _deployment-installation-physical-domain-settings-new-domain:

*Create a new UCS domain* mode
""""""""""""""""""""""""""""""

.. index::
   single: hostname; Create new UCS domain

After you selected :ref:`deployment-installation-physical-domain-settings-new`,
system setup asks for the following information,
see :numref:`deployment-installation-physical-domain-settings-new-domain-figure`:

.. _deployment-installation-physical-domain-settings-new-domain-organization:

Organization name
   You can *optionally* specify an organization name.
   The system setup uses the organization name in the second step
   to automatically generate a domain name and the LDAP base.

.. _deployment-installation-physical-domain-settings-new-domain-email:

Email address
   If you provide a valid email address,
   system setup uses it to activate a personalized license.
   Univention App Center requires the license to install apps.
   Univention automatically generates the license
   and immediately sends it to the specified email address.
   You import the license through the *Welcome* management module,
   see :external+uv-ucs-manual:ref:`central-license`
   in :cite:t:`ucs-manual`.

   .. TODO: Replace link to license management module after it's available in the document.

.. _deployment-installation-physical-domain-settings-new-domain-fqdn:

Fully qualified domain name
   Provide the fully qualified domain name for the system, including hostname and domain name.
   System setup derives the name of the Nubus for UCS system
   and the DNS domain from it.
   System setup automatically generates a suggestion if you provided an
   :ref:`deployment-installation-physical-domain-settings-new-domain-organization`.
   For the naming convention of the hostname,
   see :ref:`deployment-installation-physical-domain-settings-naming`.

   .. important::

      Recommendation: don't use publicly available DNS domains for the DNS domain,
      because this can result name resolution problems.

.. _deployment-installation-physical-domain-settings-new-domain-ldap-base:

LDAP base
   You need to define an LDAP base needs for the initialization of the directory service.
   System setup automatically creates a suggestion from the
   :ref:`deployment-installation-physical-domain-settings-new-domain-fqdn`.
   You can usually accept the suggestion without changes.

.. _deployment-installation-physical-domain-settings-new-domain-figure:

.. figure:: /images/installer-hostname.*
   :alt: Specify of hostname and LDAP base

   Specify of hostname and LDAP base

.. _deployment-installation-physical-domain-settings-ad-member:

*Join an existing Active Directory domain* mode
"""""""""""""""""""""""""""""""""""""""""""""""

.. index::
   single: hostname; Join existing Active Directory domain

If you configured the DNS server of an Active Directory domain during the
:ref:`network configuration <deployment-installation-physical-network-configuration>`,
system setup automatically suggest the name of the Active Directory domain controller in the *Active Directory account information* step,
see :numref:`deployment-installation-physical-domain-settings-ad-member-figure`.
If the suggestion is incorrect,
you can provide the name of another Active Directory domain controller or another Active Directory domain.

You need to provide an Active Directory account and its corresponding password
to enable your Nubus for UCS system to join the Active Directory domain.
The user account must have the permission to join new systems in the Active Directory domain.

In addition, you need to define a hostname for the Nubus for UCS system.
You can adopt the suggested hostname or provide a different one.
For the naming convention of the hostname, refer to :ref:`installation-domain-hostname-naming`.

System setup automatically derives the system's domain name from the domain DNS server.
In some scenarios, for example, it may be necessary to use a specific fully qualified domain name.
The Nubus for UCS system joins the Active Directory domain with the specified hostname.
After the configuration is complete, you **can't** change the domain.

In a Nubus for UCS domain, you can install systems in different *system roles*.
The first Nubus for UCS system that joins an Active Directory domain,
automatically has the :term:`UCS Primary Directory Node` system role.
If you select this mode during the installation of addition Nubus for UCS system,
system setup shows the selection dialog for the system role.
For the system role selection,
see :ref:`deployment-installation-physical-domain-settings-join-ucs`.

.. _deployment-installation-physical-domain-settings-ad-member-figure:

.. figure:: /images/installer-adjoin.*
   :alt: Information on the Active directory domain

   Information on the Active directory domain

.. _deployment-installation-physical-domain-settings-join-ucs:

*Join an existing UCS domain* mode
"""""""""""""""""""""""""""""""""""""""""

.. index::
   single: hostname; Join existing UCS domain

To join an existing Nubus for UCS domain,
you need to process the following steps:

#. Select the system role.

   In a Nubus for UCS domain, you can install systems in different *system roles*.
   The first system in a Nubus for UCS domain always has the :term:`UCS Primary Directory Node` system role.
   Additional Nubus for UCS systems can join the domain at a later point in time.
   You can assign them one of the following system roles.

   Backup Directory Node
      The :term:`Backup Directory Node` is the fallback system for the UCS Primary Directory Node.
      If the Primary Directory Node fails,
      a Backup Directory Node can adopt the role of the UCS Primary Directory Node permanently.
      Backup Directory Nodes have all the domain data and SSL security certificates saved as read-only copies.

   Replica Directory Node
      Servers with the :term:`Replica Directory Node` role have all the domain data saved as read-only copies.
      In contrast to the Backup Directory Node, however, they don't have all security certificates.
      Services running on a Replica Directory node access LDAP directory data through the local LDAP directory service.
      Replica Directory Node systems are ideal for site servers and the distribution of high-load services.

   Managed Node
      :term:`Managed Node`\ s are Nubus for UCS systems without a local LDAP directory service.
      They access domain data through other servers in the domain.
      They're suitable for services that don't require a local database for authentication,
      for example, print and file servers.

#. After you selected the system role for Nubus for UCS,
   the system setup asks for more information to join the domain,
   see :numref:`deployment-installation-physical-domain-settings-join-ucs-figure`.

   Start join at the end of the installation
      If you don't intend to let the system setup run the domain join automatically during the installation,
      deactivate the option *Start join at the end of the installation*.

   Search Primary Directory Node in DNS
      System setup automatically determines the name of the UCS Primary Directory Node
      if you provided it as DNS server during
      :ref:`deployment-installation-physical-network-configuration`.

      .. TODO: Clarify: What's the reason? Why have the detection and why deactivate it?

      If you decide to join another Nubus for UCS domain,
      you can deactivate *Search Primary Directory Node in DNS*
      and provide the fully qualified domain name of the preferred UCS Primary Directory Node.

   .. _deployment-installation-physical-domain-settings-join-ucs-credentials:

   Credentials for domain administrator
      The domain join process needs to access information about the domain.
      To grant system setup the appropriate permission,
      you need to provide the credentials for an *Administrator* account of the domain.

#. Finally, provide a hostname for the Nubus for UCS system.
   You can adopt the suggested hostname or change it.
   For the naming convention of the hostname,
   see :ref:`deployment-installation-physical-domain-settings-naming`.
   The system setup automatically derives the domain name of the computer from the domain DNS server.
   In some scenarios, such as a public mail server, it may be necessary to use a certain fully qualified domain name.
   After you completed the configuration,
   you can't change the domain name.

.. _deployment-installation-physical-domain-settings-join-ucs-figure:

.. figure:: /images/installer-join.*
   :alt: Information on the domain join

   Information on the domain join

.. _deployment-installation-physical-confirm-settings:

Confirm the installation settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Confirm configuration settings* shows a summary of your settings,
see :numref:`deployment-installation-physical-confirm-settings-summary-figure`.

Update system after installation
   The *Update system after installation* option allows the automatic installation of available errata updates.

   In addition,
   the :term:`UCS Primary Directory Node` installs all available patch level updates and errata updates.
   All other system roles update their patch level version
   to match the patch level version of the UCS Primary Directory Node.
   You need to sign in to the UCS Primary Directory Node
   to check the installation status.
   For sign-in, use the same administrator credentials
   that you provided in :ref:`deployment-installation-physical-domain-settings-join-ucs-credentials`.

.. TODO: Clarify. Is that true with the updates on the Primary? I don't think all of this happens during a join of an additional system to the domain. It would require major planning of maintenance windows when adding one system to a large domain. I can't imagine that our product requires that.

If the settings match your intention,
click :guilabel:`Configure System`
to start the configuration of the Nubus for UCS system.

System setup shows the progress during the system configuration.
It saves the installation protocol in the following files:

* :file:`/var/log/installer/syslog`
* :file:`/var/log/univention/management-console-module-setup.log`

After you confirm the completion of the system setup,
your Nubus for UCS system is ready for the first bull boot procedure.
You can restart it.
The system then boots from the hard drive.
After the boot procedure completes,
the ``root`` and ``Administrator`` users can sign in to the *Portal*,
see :external+uv-nubus-manual:ref:`nubus-portal`
in :cite:t:`uv-nubus-manual`.

.. _deployment-installation-physical-confirm-settings-summary-figure:

.. figure:: /images/installer-overview.*
   :alt: Installation overview

   Installation overview

.. _deployment-installation-physical-open-portal:

Open the portal
---------------

To open the *Portal* in Nubus for UCS,
choose any UCS system in your Nubus for UCS domain
and enter its fully qualified hostname into the browser address bar.
Your client must be able to resolve the hostname through DNS.
If your client can't resolve the DNS name,
you can use the IP address.

.. _deployment-installation-physical-license-import:

License import after installation
---------------------------------

If you installed the system as the first system in the Nubus for UCS domain
in the UCS Primary Directory Node role,
you can import the license for the domain,
see :external+uv-ucs-manual:ref:`central-license`
in :cite:t:`ucs-manual`.

.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-installation-methods:

Installation methods
====================

This section covers the various methods available
to install Nubus for Univention Corporate Server (UCS) across different infrastructure environments.
Whether deploying on physical servers, virtual machines,
cloud platforms, or systems with specific configurations,
the following sections provide step-by-step instructions
for each installation method.

Choose the installation method that best matches your deployment environment:

Physical and Virtual Machine Installation
   The standard interactive installation from DVD for traditional on-premises hardware and hypervisor environments.

Text Mode Installation
   An alternative text-based installer for systems with graphical interface compatibility issues.

Cloud Deployment
   Amazon EC2-based installation using pre-configured machine images, suitable for cloud-native deployments.

VMware-Specific Considerations
   Platform-specific configuration and driver requirements for VMware environments.

Secure Boot
   Prerequisites for installing and running Nubus for UCS
   on systems with UEFI Secure Boot enabled.

Each method guides you through the same core configuration steps:
network setup, hard drive partitioning, hostname and domain naming,
and the domain configuration.
The installation process is interactive
and prompts you for all necessary system settings.

.. _deployment-installation-download:

Installation image download
---------------------------

Download the Nubus for UCS installation image from the
`Univention website <https://www.univention.com/products/download/>`_.
The download page offers ISO and virtual machine images
for the latest patch level release.

If you are adding a system to an existing domain,
the image must match the patch level of your :term:`UCS Primary Directory Node`.
If the Primary is already at the latest patch level,
download the image directly from the download page.

If you can't update the Primary yet,
navigate to the parent directory of the download link
after you accept the terms of use and the privacy policy on the download page.
The parent directory contains images for all available patch level releases.
Select the image that matches your Primary's patch level.

For more information about the patch level requirement,
see :ref:`deployment-domain-setup-join-ucs`.

.. _deployment-installation-physical:

Physical and virtual machine installation
-----------------------------------------

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
For prerequisites and known limitations,
see :ref:`deployment-installation-secure-boot`.

.. important::

   Univention doesn't support the simultaneous operation of UCS and Debian on a UEFI system.

   The reason for this is the GRUB boot loader of Nubus for UCS
   that partly uses the same configuration files as Debian.

   An already installed Debian leads to the fact
   that the hardware can't boot Nubus for UCS anymore
   after the installation of or an update to UCS 5.3.
   A subsequent installation of Debian also results in Nubus for UCS 5.3 not being able to boot.

Besides operating Nubus for UCS on hardware or in a virtualization solution,
you can also install it on the Amazon EC2 cloud using an AMI image.
For more information,
see :ref:`deployment-installation-cloud`.

You can use the installation interfaces with a keyboard and with mouse.

* Use the :kbd:`Tab` key to jump to the next field.

* Use the :kbd:`Shift+Tab` keys to jump back to the previous field.

* Use the :kbd:`Enter` key to assign values to the input field and confirm buttons.

* Use the arrow keys inside a list or table for navigating between entries.

* Use :guilabel:`Cancel` to cancel the current configuration step.
  You can select a previous configuration step again in the menu
  that the installer shows subsequently.
  Under certain circumstances,
  you can't directly select subsequent configuration steps
  if you haven't completed previous steps.

To continue the installation,
follow steps in
:ref:`deployment-initial-system-configuration`.

.. _deployment-installation-text-mode:

Text mode installation
----------------------

On systems that show problems with the graphical Univention installer,
you can start the installation in text mode.
For text mode, select :ref:`deployment-initial-system-configuration-install-mode-text-mode`
in the installation boot prompt.

During installation in text mode
the installer shows the same information and asks for the same settings,
see
:ref:`deployment-initial-system-configuration`.
After hard drive partitioning, the system is ready for the first boot
and the installer restarts the system.

After restart,
you can resume the configuration with the system setup in a web browser.
Open the URL :samp:`https://{SERVER-IP-ADDRESS}` in your web browser.
System setup requires authentication with the user ``root``.
It then asks for location and network setting.
You continue with the same steps as the graphical installer,
see :ref:`deployment-domain-setup`.

.. _deployment-installation-cloud:

Cloud deployment
----------------

Univention provides an Amazon Machine Image (AMI) for the Amazon EC2 cloud for Nubus for UCS.
You can use this generic image for all Nubus for UCS system roles
to derive an individual instance
that you can configure through management modules regarding topics such as domain name and software selection.

For information about the setup process of a Nubus for UCS instance based on Amazon EC2,
see :uv:help:`Amazon EC2 Quickstart <21833>`.

.. _deployment-installation-vmware:

VMware-specific considerations
------------------------------

If you install Nubus for UCS as a guest in VMware,
select the option :menuselection:`Linux --> Debian` as the *Guest operating system*,
because Nubus for UCS builds on Debian GNU/Linux.

The Linux kernel in Nubus for UCS includes all the support drivers necessary for operation in VMware,
such as :file:`vmw_balloon`, :file:`vmw_pvsci`, :file:`vmw_vmci`, :file:`vmwgfx`, and :file:`vmxnet3`.

Nubus for UCS delivers the :program:`Open VM Tools`.
You can install them through the :program:`open-vm-tools` package.
The package is optional,
but necessary for features such as automatic time synchronization
between the virtualization server and the guest system.

.. _deployment-installation-secure-boot:

Secure Boot
-----------

Nubus for UCS supports UEFI Secure Boot.
You don't need to deactivate Secure Boot before installing from the DVD.

Secure Boot relies on a chain of trust
where the system firmware verifies each component before loading it.
On Nubus for UCS, this chain works as follows:

#. The UEFI firmware loads :program:`shim`,
   a *first-stage boot loader* signed by Microsoft.
   The firmware verifies :program:`shim` against the certificates
   in the firmware's trust store.

#. :program:`shim` loads the Debian-signed :program:`GRUB` boot loader.
   :program:`shim` verifies :program:`GRUB`
   using Debian's key embedded at build time
   and checks the *Secure Boot Advanced Targeting (SBAT) revocation level*.

#. :program:`GRUB` loads the Linux kernel, also signed by Debian.

Because Nubus for UCS builds on Debian GNU/Linux,
it uses Debian's signed boot components.
The following conditions in the current Debian Secure Boot tool chain
can prevent a successful boot on certain hardware.

SBAT revocation level
~~~~~~~~~~~~~~~~~~~~~

The *Secure Boot Advanced Targeting (SBAT) revocation level*
controls which boot loader versions the firmware accepts.

The :program:`GRUB` boot loader on the Nubus for UCS installation media
declares SBAT generation ``grub,4``.
Some systems have a higher *SBAT revocation level* stored in their firmware,
which causes them to reject this :program:`GRUB` version.

A system can have an elevated SBAT level for the following reasons:

* A previous Microsoft Windows installation raised the SBAT level to ``grub,5``
  through a Windows Update firmware update.

* A previous Linux distribution with a newer :program:`GRUB` version
  raised the SBAT level.

The *SBAT revocation level* persists in UEFI firmware memory (NVRAM).
Removing the previous operating system doesn't clear it.

Systems that have never had their SBAT level raised aren't affected.

If the system rejects the boot loader with a *Security Violation* error,
deactivate Secure Boot in the firmware setup before installation.

.. note::

   Tools such as :program:`Rufus` version 4.6 and later
   check the SBAT generation proactively
   and display a *revoked UEFI bootloader* warning.
   This warning indicates a potential incompatibility,
   not a security problem with the Nubus for UCS installation media.

Firmware certificate requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :program:`shim` boot loader on the Nubus for UCS installation media
is signed with the *Microsoft Corporation UEFI CA 2011* certificate.
The firmware must include this certificate in its trust store
to verify :program:`shim` before loading it.

Most systems ship with this certificate pre-installed.
However, some hardware released in 2024 and later
ships only with the newer *Microsoft UEFI CA 2023* certificate
and doesn't include the 2011 certificate.

On these systems, the firmware doesn't recognize :program:`shim`
and refuses to boot from the installation media.

To install Nubus for UCS on affected hardware,
use one of the following approaches:

* Enroll the *Microsoft Corporation UEFI CA 2011* certificate
  in the firmware setup.

* Deactivate Secure Boot in the firmware setup before installation.

This limitation affects the entire Debian ecosystem.
Debian resolves it when it ships a :program:`shim` version
signed with the *Microsoft UEFI CA 2023* certificate.

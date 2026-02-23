.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-boot-manager:

Boot manager
============

In Nubus for UCS, GRUB serves as the boot manager.
GRUB provides a menu where you can select which Linux kernel to boot.
It can also access file systems directly
and load an alternative kernel if the primary kernel fails to boot,
so you can recover without external media.
See :numref:`system-administration-boot-manager-figure` for an example of the GRUB menu interface.

.. _system-administration-boot-manager-figure:

.. figure:: /images/computers_grub.*
   :alt: GRUB boot manager menu

   GRUB boot manager menu

.. seealso::

   `GRUB <https://www.gnu.org/software/grub/manual/grub/>`_
      for the documentation of GRUB.

.. _system-administration-boot-manager-loading:

Boot loading process
--------------------

GRUB loads in two stages.
Your system stores the first stage in the firmware boot area.
This is either the Master Boot Record (BIOS)
or the EFI System Partition (UEFI).
The first stage then loads the second stage, which handles the boot menu and kernel loading.
See the :ref:`system-administration-boot-manager-kernel-selection` section
for information on how to interact with the boot menu during startup.

.. _system-administration-boot-manager-kernel-selection:

Kernel selection
----------------

GRUB stores kernel selection options in the file :file:`/boot/grub/grub.cfg`.
GRUB automatically generates this file from your system configuration and kernel packages,
so don't edit it manually.
The boot menu automatically shows all installed kernel packages.

During the boot process, GRUB displays a menu with the available kernel options.
GRUB selects the first kernel by default.
Use the arrow keys to navigate between options.
Press :kbd:`Enter` to boot the selected kernel.
If you don't select a kernel within 5 seconds,
GRUB automatically boots the default kernel.
You can customize this timeout
in the :ref:`system-administration-boot-manager-configuration` section.

You can start the memory test program :command:`Memtest86+x64.bin`
by selecting the option :guilabel:`Memory test` from the boot menu.
Use this to diagnose potential memory issues
if you experience system instability or crashes.
If :command:`Memtest86+x64.bin` detects errors,
your system likely has faulty RAM that needs replacement.

.. _system-administration-boot-manager-configuration:

Configuration
-------------

To configure GRUB, you need root privileges.
You can configure GRUB using the command line or the *Management UI*.

.. TODO: Add cross-reference to the "How to set UCR variables" section
   For now, document that these variables can be changed via UCR.

By default, you have five seconds to select a kernel to boot.
You can customize this delay using the :term:`UCR variable` :envvar:`grub/timeout`.
For available timeout options and their behavior,
refer to the :envvar:`grub/timeout` variable documentation.

By default, the screen displays at ``800x600`` pixels with 16-bit color depth.
You can change this resolution using the UCR variable :envvar:`grub/gfxmode`.
You can only use resolutions that your system's VESA BIOS supports.
Before finalizing resolution changes,
test them carefully
and ensure you can access the system in recovery mode if needed.
The format for specifying a resolution is :samp:`{HORIZONTAL}x{VERTICAL}@{COLORDEPTHBIT}`, for example: ``1024x768@16``.
For available VESA modes, see `VESA BIOS Extensions <https://en.wikipedia.org/wiki/VESA_BIOS_Extensions>`_.

You can pass kernel options to the Linux kernel with the UCR variable :envvar:`grub/append`.
Common kernel options include serial console parameters
such as ``console=ttyS0``,
ACPI settings such as ``noacpi``,
and memory management options.
For the kernel command-line parameters,
see :external+linux-kernel-docs:ref:`kernelparameters`.

You can deactivate the splash screen—the visual representation of the boot process—by setting the UCR variable :envvar:`grub/bootsplash` to ``nosplash``.

.. TODO: Add instructions on running update-grub after configuration changes
         Cross-reference to the appropriate section explaining post-configuration steps.

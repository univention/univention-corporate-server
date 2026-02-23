.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-boot-manager:

Boot manager
============

In |UCSUCS| GNU GRUB 2 is used as the boot manager. GRUB provides a menu which
allows the selection of a Linux kernel or another operating system to be booted.
GRUB can also access file systems directly and can thus, for example, load
another kernel in case of an error.

.. _grub-selection:

.. figure:: /images/computers_grub.*
   :alt: GRUB menu

   GRUB menu

GRUB gets loaded in a two-step procedure; in the Master Boot Record of the hard
drive, the Stage 1 loader is written which refers to the data of Stage 2, which
in turn manages the rest of the boot procedure.

The selection of kernels to be started in the boot menu is stored in the file
:file:`/boot/grub/grub.cfg`. This file is generated automatically; all installed
kernel packages are available for selection. The memory test program
:command:`Memtest86+` can be started by selecting the option :guilabel:`Memory
test` and performs a consistency check for the main memory.

There is a five second waiting period during which the kernel to be booted can
be selected. This delay can be changed via the |UCSUCRV| :envvar:`grub/timeout`.

By default a screen size of ``800x600`` pixels and 16 Bit color depth is preset.
A different value can be set via the |UCSUCRV| :envvar:`grub/gfxmode`. Only
resolutions are supported which can be set via VESA BIOS extensions. A list of
available modes can be found in `VESA BIOS Extensions
<w-vesa-bios-extensions_>`_. The input must be specified in the format
:samp:`{HORIZONTAL}x{VERTICAL}@{COLOURDEPTHBIT}`, so for example
``1024x768@16``.

Kernel options for the started Linux kernel can be passed with the |UCSUCRV|
:envvar:`grub/append`. |UCSUCRV| :envvar:`grub/xenhopt` can be used to pass
options to the Xen hypervisor.

The graphic representation of the boot procedure - the so-called splash screen -
can be deactivated by setting |UCSUCRV| :envvar:`grub/bootsplash` to
``nosplash``.

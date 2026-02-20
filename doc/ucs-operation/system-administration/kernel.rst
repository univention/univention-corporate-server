.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-kernel:

Kernel
======

.. _computers-available-kernel-variants:

Available kernel variants
-------------------------

The standard kernel in UCS 5.0 is based on the Linux kernel 4.19. In principle,
there are three different types of kernel packages:

* A *kernel image package* provides an executable kernel which can be installed
  and started.

* A *kernel source package* provides the source code for a kernel. From this
  source, a tailor-made kernel can be created, and functions can be activated or
  deactivated.

* A *kernel header package* provides interface information which is required by
  external packages if these have to access kernel functions. This information
  is usually necessary for compiling external kernel drivers.

Normally, the operation of a UCS system only requires the installation of one
kernel image package.

Several kernel versions can be installed in parallel. This makes sure that there
is always an older version available to which can be reverted in case of an
error. So-called meta packages are available which always refer to the kernel
version currently recommended for UCS. In case of an update, the new kernel
version will be installed, making it possible to keep the system up to date at
any time.

.. _computers-hardware-drivers-kernel-modules:

Hardware drivers / kernel modules
---------------------------------

The boot process occurs in two steps using an initial RAM disk (*initrd* for
short). This is composed of an archive with further drivers and programs.

The GRUB boot manager (see :ref:`grub`) loads the kernel and the *initrd* into
the system memory, where the *initrd* archive is extracted and mounted as a
temporary root file system. The real root file system is then mounted from this,
before the temporary archive is removed and the system start implemented.

The drivers to be used are recognized automatically during system start and
loaded via the :program:`udev` device manager. At this point, the necessary
device links are also created under :file:`/dev/`. If drivers are not recognized
(which can occur if no respective hardware IDs are registered or hardware is
employed which cannot be recognized automatically, e.g., ISA boards), kernel
modules to be loaded can be added via |UCSUCRV| :envvar:`kernel/modules`. If
more than one kernel module is to be loaded, these must be separated by a
semicolon. The |UCSUCRV| :envvar:`kernel/blacklist` can be used to configure a
list of one or more kernel modules for which automatic loading should be
prevented. Multiple entries must also be separated by a semicolon.

Unlike other operating systems, the Linux kernel (with very few exceptions)
provides all drivers for hardware components from one source. For this reason,
it is not normally necessary to install drivers from external sources
subsequently.

However, if external drivers or kernel modules are required, they can be
integrated via the DKMS framework (Dynamic Kernel Module Support). This provides
a standardized interface for kernel sources, which are then built automatically
for every installed kernel (insofar as the source package is compatible with the
respective kernel). For this to happen, the kernel header package
:program:`linux-headers-amd64` must be installed in addition to the
:program:`dkms` package. Please note that not all the external kernel modules
are compatible with all kernels.

.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-kernel:

Kernel
======

The Linux kernel is the core of your operating system.
It manages hardware resources like processors, memory, and devices,
and enables communication between software applications and hardware.

As a system administrator, you configure the kernel to support your hardware
and optimize system performance.
This section explains kernel packages, kernel versions, and kernel modules,
and shows you how to manage drivers and custom kernel functionality
in Nubus for UCS.

.. _system-administration-kernel-packages:

Kernel packages
---------------

The :external+uv-docs-overview:ref:`release-notes` contain
information about the standard kernel version for each Nubus for UCS minor version.
The Release Notes document the kernel version used, starting with the initial patch level release ``-0``.
Typically, a Nubus for UCS system requires only one installed kernel image package.
Nubus for UCS uses the following types of kernel packages:

Kernel image package
   A *kernel image package* provides an executable kernel
   that you can install and run.

Kernel source package
   A *kernel source package* provides kernel source code.
   With it, you can create a customized kernel and activate or deactivate functions.

Kernel header package
   A *kernel header package* provides the interface definitions
   that external software needs to access kernel functions.
   You need this to compile external kernel drivers.

.. _system-administration-kernel-versions:

Version management
------------------

You can install several kernel versions in parallel.
This ensures you always have an older version available if you need to revert after an error.
Univention provides meta packages that always point to the recommended kernel version for Nubus for UCS.
When you update the system, the system installs the new kernel version automatically, keeping your system current.

.. _system-administration-kernel-modules:

Kernel modules and drivers
---------------------------

The kernel relies on modules and drivers to communicate with hardware and enable system functionality.
This section explains how the boot process loads drivers,
how you configure additional kernel modules,
and how to integrate external drivers into your system.

.. _system-administration-kernel-modules-loading:

Boot process and driver loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The boot process involves several stages.
The boot loader loads the kernel and an initial RAM disk, *initrd* for short, into system memory.
The *initrd* is a compressed archive containing essential drivers and programs.

The system then extracts and mounts the *initrd* archive as a temporary root file system.
Within this temporary environment, the system initializes hardware,
loads additional drivers as needed,
and locates the real root file system on disk.
After mounting the real root file system,
the system switches to it and removes the temporary *initrd* from memory.

The GRUB boot manager handles the first stage of loading the kernel and *initrd*.
For more information about GRUB configuration,
see :external+uv-ucs-manual:ref:`grub`.

.. TODO: Replace to cross-reference of grub once the content exists in this document.

.. _system-administration-kernel-modules-detection:

Automatic driver detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :program:`udev` service detects and manages hardware devices automatically during system startup.
It loads drivers and creates device files in the :file:`/dev/` directory so you can access the hardware.
If the system doesn't detect the drivers you need,
you can enable kernel modules through the :term:`UCR variable` :envvar:`kernel/modules`.
This can happen if hardware vendors didn't register hardware IDs.
Use the UCR variable :envvar:`kernel/blacklist` to prevent specific kernel modules from loading automatically.
For both variables, separate multiple entries with a semicolon.

.. _system-administration-kernel-modules-standard:

Standard vs. external drivers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Linux kernel includes drivers for most common hardware.
This means you typically don't need external driver installations for standard hardware.
However, specialized hardware or newer devices might need external drivers or firmware.

.. _system-administration-kernel-modules-external:

External drivers and DKMS
~~~~~~~~~~~~~~~~~~~~~~~~~

If you need external drivers or kernel modules,
you can integrate them through the DKMS framework (Dynamic Kernel Module Support).
DKMS provides a standardized interface for kernel sources
and builds them automatically for every installed kernel.
The source package must be compatible with the kernel.
External kernel modules aren't compatible with all kernel versions.

To use DKMS, you need:

* Root privileges on the system.
* The kernel header package :program:`linux-headers-amd64`.
* The :program:`dkms` package.
* A C compiler and build tools, usually installed automatically as dependencies.

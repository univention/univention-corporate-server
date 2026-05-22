.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration:

*********************
System administration
*********************

This chapter covers low-level configuration tasks for technical administrators
managing Nubus for UCS systems.
It addresses the components that underpin every running system:
the kernel, the boot process, network connectivity, and outbound proxy access.

Univention Configuration Registry
   Manage system settings through Univention Configuration Registry (UCR),
   the central tool for managing configuration on Nubus for UCS systems.
   Configure settings using the command-line interface, the web-based management UI,
   or configuration policies that apply across multiple systems.
   UCR automatically regenerates configuration files from templates when settings change,
   eliminating the need for manual file editing.
   See :ref:`system-administration-ucr`.

Kernel
   Manage kernel packages, kernel versions, and kernel modules.
   This includes loading additional drivers, blacklisting unwanted modules,
   and integrating external drivers through Dynamic Kernel Module Support (DKMS).
   See :ref:`system-administration-kernel`.

Boot manager
   Configure GRUB, the boot manager in Nubus for UCS.
   Control the boot timeout, screen resolution, kernel options,
   and which kernel the system boots by default.
   See :ref:`system-administration-boot-manager`.

Network configuration
   Configure network interfaces and advanced network setups
   such as bridging for virtual machines, bonding for failover redundancy,
   and VLANs for logical traffic separation.
   See :ref:`system-administration-network`.

Proxy settings
   Route outbound traffic from command-line tools and Nubus for UCS update utilities
   through a proxy server using UCR variables.
   See :ref:`system-administration-proxy`.

.. toctree::
   :caption: Contents

   ucr
   logging
   diagnostics
   cron
   access-and-authentication
   regional-settings
   system-services
   kernel
   boot-manager
   network/index
   proxy

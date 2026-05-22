.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration:

*********************
System administration
*********************

This chapter covers low-level configuration and operational tasks
for technical administrators managing Nubus for UCS systems.
It includes system configuration, administrative access, regional settings,
service management, scheduled tasks, logging, diagnostics,
and platform-level topics such as the kernel, boot process,
network configuration, and proxy settings.

Univention Configuration Registry
   Manage system settings through Univention Configuration Registry (UCR),
   the central tool for managing configuration on Nubus for UCS systems.
   Configure settings using the command-line interface, the web-based management UI,
   or configuration policies that apply across multiple systems.
   UCR automatically regenerates configuration files from templates when settings change,
   eliminating the need for manual file editing.
   See :ref:`system-administration-ucr`.

Administrative access and authentication
   Manage administrative access to Nubus for UCS systems.
   This includes the local ``root`` account, SSH access,
   and PAM-based authentication restrictions for selected services.
   See :ref:`system-administration-access-authentication`.

Regional settings
   Configure language, locale, keyboard, time zone,
   and time synchronization settings for Nubus for UCS systems.
   See :ref:`system-administration-regional-settings`.

Service management and system integration
   Manage system services and configure service-related integration settings.
   This includes service startup behavior, LDAP server selection,
   print server settings, and the name service cache daemon.
   See :ref:`system-administration-system-services`.

Run recurring actions with cron
   Schedule recurring tasks on Nubus for UCS systems.
   This includes predefined cron directories, local cron jobs in
   :file:`/etc/cron.d/`, and cron jobs through Univention Configuration Registry.
   See :ref:`system-administration-cron`.

Log files and log rotation
   Find log file locations and configure log rotation on Nubus for UCS systems.
   This includes listener module log files
   and their dedicated log rotation settings.
   See :ref:`system-administration-logging`.

System diagnostics
   Inspect the current state of a Nubus for UCS system
   and diagnose common problems.
   This includes command-line system status logging
   and diagnostic functions in the *Management UI*.
   See :ref:`system-administration-diagnostics`.

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
   access-and-authentication
   regional-settings
   system-services
   cron
   logging
   diagnostics
   kernel
   boot-manager
   network/index
   proxy

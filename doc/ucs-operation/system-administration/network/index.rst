.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network:

Network configuration
=====================

The configuration of network interfaces can be adjusted with the UMC module
:guilabel:`Network settings`.

The configuration is saved in :term:`UCR variables <UCR variable>`, which can also be set
directly. These variables are listed in the individual sections.

.. _system-administration-network-figure:

.. figure:: /images/computers_network.*
   :alt: Configuring the network settings

   Configuring the network settings

This documentation covers three areas:

* **Basic network configuration** walks through setting up IPv4, IPv6,
  and DNS servers for standard network interfaces.

* **Advanced network configurations** explains specialized setups
  like bridging for virtualization, bonding for redundancy, and VLANs for logical network separation.

* **Operation procedures** covers verifying your configuration,
  troubleshooting problems, and making changes after initial setup.

All the network cards available in the system are listed under *IPv4 network
devices* and *IPv6 network devices* (only network interfaces in the
:samp:`eth{X}` scheme are shown).

Network interfaces can be configured for IPv4 and/or IPv6. IPv4 addresses have a
32-bit length and are generally written in four blocks in decimal form (e.g.,
``192.0.2.10``), whereas IPv6 addresses are four times as long and typically
written in hexadecimal form (e.g., ``2001:0DB8:FE29:DE27:0000:0000:0000:0000``).

UCS supports advanced network configurations using bridging, bonding and virtual
networks (VLAN):

* Bridging is often used with virtualization to connect multiple virtual
  machines running on a host through one shared physical network interface.

* Bonding allows failover redundancy for hosts with multiple physical network
  interfaces to the same network.

* VLANs can be used to separate network traffic logically while using only one
  (or more) physical network interface.

.. toctree::

   basic
   advanced
   operational

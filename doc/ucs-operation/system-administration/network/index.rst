.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network:

Network configuration
=====================

This chapter covers network configuration in Nubus for UCS.
You can adjust network interface configuration in the *Network settings* management module,
located at :menuselection:`System --> Network settings` in the *Management UI*.
:numref:`system-administration-network-figure` shows the management module.

.. _system-administration-network-figure:

.. figure:: /images/computers_network.*
   :alt: Configure network configuration in the Network settings module

   Configure network configuration in the *Network settings* module

The management module lists all available network cards in *IPv4 network devices*
and *IPv6 network devices*.
It displays only network interfaces in the :samp:`eth{X}` scheme.
Beyond basic configuration,
Nubus for UCS supports the following advanced network configurations.
:numref:`system-administration-network-decision-table` shows common scenarios and the appropriate technique for each.

Bridging
   Bridging lets you connect multiple virtual machines running on a host
   through one shared physical network interface for virtualization.

Bonding
   Bonding provides failover redundancy for hosts
   with multiple physical network interfaces to the same network.

Virtual networks (VLANs)
   VLANs separate network traffic logically
   while using one or more physical network interfaces.

.. _system-administration-network-decision-table:

.. list-table:: Common network configuration scenarios
   :header-rows: 1
   :widths: 7 2 3

   * - Your need
     - Technique
     - Where to find it

   * - Bridge virtual machines to the network.
     - Bridging
     - :ref:`system-administration-network-bridge`

   * - Bond multiple network cards for failover.
     - Bonding
     - :ref:`system-administration-network-bonding`

   * - Separate traffic on one physical network.
     - VLAN
     - :ref:`system-administration-network-vlan`

.. toctree::
   :caption: Contents

   basic
   advanced

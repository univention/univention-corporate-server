.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network-advanced:

Advanced network configurations
-------------------------------

Advanced network configurations address specialized scenarios
where standard single-interface setups don't meet your needs.
You can combine multiple network interfaces for redundancy (bonding),
connect virtual machines to physical networks (bridging),
or logically separate network traffic (VLAN).
These techniques require careful planning and may require switch configuration.

.. _system-administration-network-bridge:

Configure bridging
------------------

.. index::
   single: network; bridge
   single: network; switch
   pair: bridge; network

The most common application scenario for *bridging* is the shared use of a
physical network card by one or more virtual machines. Instead of one network
card for each virtual machine and the virtualization server itself, all systems
are connected via a shared uplink. A bridge can be compared with a switch
implemented in software which is used to connect the individual hosts together.
The hardware network adapter used is called a *bridge port*.

In order to configure a bridge, ``Bridge`` must be selected as the *Interface
type* under :guilabel:`Add`. The *Name of new bridge interface* can be selected
at will. Then click on :guilabel:`Next`.

The physical network card intended to act as the uplink can be selected under
*Bridge ports*. In the typical scenario of connecting virtual machines
via just one network card, there is no risk of a network loop. If the bridge is
used to connect two Ethernet networks, the spanning tree protocol (STP) is
employed to avoid network loops. The Linux kernel only implements STP, not the
Rapid STP or Multiple STP versions.

The *Forwarding delay* setting configures the waiting time in seconds during
which information is collected about the network topology when a connection is
being made via STP. If the bridge is used for connecting virtual machines to one
physical network card, STP should be disabled by setting the value to ``0``.
Otherwise problems may occur when using DHCP, as the packets sent during the
waiting time are not forwarded.

The *Additional bridge options* input field can be used to configure arbitrary
bridge parameters. This is only necessary in exceptional cases; an overview of
the possible settings can be found on the manual page
`bridge-utils-interfaces(5)
<https://manpages.debian.org/bookworm/bridge-utils/bridge-utils-interfaces.5.en.html>`_.

Clicking on :guilabel:`Next` offers the possibility of optionally assigning the
bridge an IP address. This interface can then also be used as a network
interface for the virtualization host. The options are the same as described in
:ref:`system-administration-network-ipv4` and :ref:`system-administration-network-ipv6`.

.. _system-administration-network-bonding:

Configure bonding
-----------------

.. index::
   single: network; bonding
   single: network; link aggregation
   pair: bonding; network
   single: network; etherchannel
   single: network; teaming
   single: network; trunking


*Bonding* can be used to bundle two (or more) physical network cards in order to
increase the performance or improve redundancy in failover scenarios.

In order to configure a bonding, ``Bonding`` must be selected as the *Interface
type* under :guilabel:`Add`. The *Name of the bonding interface* can be selected
at will. Then click on :guilabel:`Next`.

The network cards which form part of the bonding interface are selected under
*Bond slaves*. The network cards which should be given preference in failover
scenarios (see below) can be selected via *Bond primary*.

The *Mode* configures the distribution of the network cards within the bonding:

* ``balance-rr (0)`` distributes the packets equally over the available network
  interfaces within the bonding one after the other. This increases performance
  and improves redundancy. In order to use this mode, the network switches used
  must support *link aggregation*.

* When ``active-backup (1)`` is used, only one network card is active for each
  bonding interface (by default this is the network interface configured in
  *Bond primary*). If the primary network card fails, this is detected by the
  Linux kernel, which switches to another card in the bonding. This version
  increases redundancy. It can be used with every network switch.

In addition, there are also a number of other bonding methods. These are
generally only relevant for special cases and are described under `Linux
Ethernet Bonding Driver HOWTO <https://www.kernel.org/doc/Documentation/networking/bonding.txt>`_.

The Media Independent Interface (MII) of the network cards is used to detect
failed network adapters. The *MII link monitoring frequency* setting
specifies the testing interval in milliseconds.

All other bonding parameters can be configured under *Additional bonding
options*. This is only necessary in exceptional cases; an overview of the
possible settings can be found under `Linux Ethernet Bonding Driver HOWTO
<https://www.kernel.org/doc/Documentation/networking/bonding.txt>`_.

Clicking on :guilabel:`Next` allows to optionally assign the bonding interface
an IP address. If one of the existing network cards which form part of the
bonding interface has already been assigned an IP address, this configuration
will be removed. The options are the same as described in :ref:`system-administration-network-ipv4`
and :ref:`system-administration-network-ipv6`.

.. _system-administration-network-vlan:

Configure VLAN
--------------

.. index::
   pair: network; vlan
   single: network; 802.1q

VLANs can be used to separate the network traffic in a physical network
logically over one or more virtual subnetworks. Each of these virtual networks
is an independent broadcast domain. This makes it e.g. possible to differentiate
between a network for the employees and a guest network for visitors in a
company network although they use the same physical cables. The individual end
devices can be assigned to the VLANs via the configuration of the switches. The
network switches must support 802.1q VLANs.

A distinction is made between two types of connections between network cards:

* A connection only transports packets from a specific VLAN. In this case,
  untagged data packets are transmitted.

  This is typically the case if only one individual end device is connected via
  this network connection.

* A connection transports packets from several VLANs. This is also referred to
  as a trunk link. In this case, each packet is assigned to a VLAN using a VLAN
  ID. During transmission between trunk links and specific VLANs, the network
  switch takes over the task of filtering the packets by means of the VLAN IDs
  as well as adding and removing the VLAN IDs.

  This type of connection is primarily used between switches/servers.

  Some switches also allow the sending of packets with and without VLAN tags
  over a shared connection, but this is not described in more detail here.

When configuring a VLAN in the UMC module :guilabel:`Network settings` it is
possible to configure for a computer which VLANs it wants to participate in. An
example here would be an internal company web server, which should be available
both to the employees and any users of the guest network.

In order to configure a VLAN, ``Virtual LAN`` must be selected as the *Interface
type* under :guilabel:`Add`. The network interface for which the VLAN is
specified with *Parent interface*. The *VLAN ID* is the unique identifier of the
VLAN. Valid values are from 1 to 4095. Then :guilabel:`Next` must be clicked.

Clicking on :guilabel:`Next` allows to optionally assign the VLAN interface an
IP address. The options are the same as described in :ref:`system-administration-network-ipv4` and
:ref:`system-administration-network-ipv6`. When assigning an IP address, ensure that the address
matches the assigned VLAN address range.

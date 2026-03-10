.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network-advanced:

Advanced network configurations
-------------------------------

Advanced network configurations address specialized network scenarios
beyond basic single-interface setups.
They require you to plan carefully
and configure your network switches,
but provide benefits:

* Performance improvements through load distribution and bonding.
* Redundancy and failover protection for critical systems.
* Network isolation and security through VLANs.
* Virtualization support through bridging.

Three main techniques are available,
and you must configure your network switches to support each:

Bridging
   Connect virtual machines to physical networks,
   see :ref:`system-administration-network-bridge`.

Bonding
   Combine multiple network interfaces for redundancy,
   see :ref:`system-administration-network-bonding`.

VLAN
   Logically separate network traffic,
   :ref:`system-administration-network-vlan`.

.. _system-administration-network-bridge:

Configure bridging
~~~~~~~~~~~~~~~~~~

*Bridging* allows multiple systems to share one physical network card.
Instead of needing one network card per virtual machine plus one for the host,
you can run all systems through a single uplink.
The *bridge port* is the hardware network adapter that carries this traffic.

To configure a bridge in the *Network settings* management module,
click :guilabel:`Add`
and select ``Bridge`` as the *Interface type*.
Enter a name for the new bridge interface in the *Name of new bridge interface* field.
Click :guilabel:`Next`.
You see the following fields:

Bridge ports
   In *Bridge ports*, select the physical network card to act as the uplink.
   If the bridge connects two Ethernet networks,
   enable the Spanning Tree Protocol (STP) to avoid network loops.
   If you're connecting only virtual machines through a single network card,
   you don't have a risk of a network loop.

   .. note::

      The Linux kernel supports only STP, not Rapid STP or Multiple STP.

      Make sure your network switch and virtualization host support bridge operation.
      Your network switch's configuration might interfere with Linux bridge STP.

Forwarding delay
   The *Forwarding delay* setting determines how long STP waits before activating the bridge.

   When bridging virtual machines through a single network card,
   set this value to ``0`` to deactivate STP.
   If STP is active, DHCP may fail because the bridge delays packet forwarding while STP converges.

Additional bridge options
   Use *Additional bridge options* to configure optional bridge parameters.
   You only need this for specialized network configurations.
   For a complete list of available settings,
   see the `bridge-utils-interfaces(5) manual page <https://manpages.debian.org/bookworm/bridge-utils/bridge-utils-interfaces.5.en.html>`_.

If you want to assign an IP address to the bridge, click :guilabel:`Next`.
Do this if the virtualization host needs network access through the bridge.
For IP configuration options, see :ref:`system-administration-network-ipv4` and :ref:`system-administration-network-ipv6`.

.. _system-administration-network-bonding:

Configure bonding
~~~~~~~~~~~~~~~~~

Use *bonding* to combine two or more network cards for:

* Increased performance through load distribution.
* Failover redundancy if one card fails.

To configure bonding in the *Network settings* management module,
click :guilabel:`Add`
and select ``Bonding`` as the *Interface type*.
Enter a name for the bonding interface in the *Name of the bonding interface* field.
Click :guilabel:`Next`.
You see the following fields:

.. _system-administration-network-bonding-slaves:

Bond slaves
   In *Bond slaves*, select the network cards that are part of the bonding interface.

.. _system-administration-network-bonding-primary:

Bond primary
   In *Bond primary*, select the network card to prioritize during failover.
   The system switches to a backup card if the primary card fails.

Mode
   The *Mode* setting determines how bonded network cards distribute traffic.
   Choose a mode based on your redundancy requirements
   and network switch capabilities:

   * ``balance-rr (0)`` distributes packets equally across all bonded network cards in round-robin fashion.
     This increases performance and provides redundancy.
     Network switches must support link aggregation.

   * ``active-backup (1)`` keeps only one network card active at a time.
     By default, this is the network card you selected in :ref:`system-administration-network-bonding-primary`.
     If the active card fails, the Linux kernel automatically switches to another card.
     This mode provides redundancy and works with any network switch.

   For other bonding modes,
   see :external+linux-kernel-docs:doc:`networking/bonding`.

MII link monitoring frequency
   The Linux kernel checks network card status using the Media Independent Interface (MII).
   This setting specifies the interval in milliseconds between health checks.

Additional bonding options
   You only need *Additional bonding options* in exceptional cases.
   For an overview of the possible settings,
   see :external+linux-kernel-docs:doc:`networking/bonding`.

If you want to assign an IP address to the bonding interface,
click :guilabel:`Next`.

Creating a bond automatically removes any existing IP addresses from the network cards.
You can assign an IP address to the bonding interface after creation.
For configuration options, see :ref:`system-administration-network-ipv4` and :ref:`system-administration-network-ipv6`.

.. _system-administration-network-vlan:

Configure VLAN
~~~~~~~~~~~~~~

Virtual local area networks (VLANs) separate network traffic logically within a single physical network.
Each VLAN is an independent broadcast domain.
For example, you can run both employee and guest networks on the same physical cables.
Configure your network switches to assign devices to their respective VLANs.
Your switches must support 802.1q VLANs.

Network connections use one of two VLAN modes.
Choose based on how many VLANs your system needs to access:

Untagged (access port)
    This mode transports packets from a single VLAN only.
    Packets travel without a VLAN tag.
    Use this mode when a single device connects to only one VLAN,
    typical for user workstations.

Tagged (trunk port)
    This mode transports packets from multiple VLANs.
    Each packet carries a VLAN ID that identifies which VLAN the packet belongs to.
    The switch uses this ID to filter and route traffic correctly.
    During transmission, the switch adds or removes VLAN tags as packets cross VLAN boundaries.
    Use this mode when a single system needs to access or serve multiple VLANs,
    such as network servers and switches.

In the *Network settings* management module,
you can assign computers to one or more VLANs.
For example, a web server can access both the employee and guest networks.

To configure a VLAN, follow these steps:

#. In the *Network settings* management module,
   click :guilabel:`Add`
   and select ``Virtual LAN`` as the *Interface type*.

#. In *Parent interface*,
   select the physical network interface that hosts this VLAN.

#. In *VLAN ID*, enter the unique identifier for this VLAN.
   The valid range is ``1`` to ``4095``.
   Coordinate with your network administrator
   to ensure each VLAN has a unique ID that matches your network switch configuration.

#. If you want to assign an IP address to the VLAN interface, click :guilabel:`Next`.
   Configure the IP address using the same options available for regular network interfaces.
   Ensure the IP address matches the VLAN address range.
   For details, see :ref:`system-administration-network-ipv4` and :ref:`system-administration-network-ipv6`.

.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network-basic:

Basic network configuration
---------------------------

Basic network setup involves three steps:

#. Connect your Nubus for UCS system to a network.
#. Configure IPv4 and/or IPv6 addresses.
#. Define name servers.

These settings apply to standard network interfaces such as ``eth0`` and ``eth1``.

.. _system-administration-network-ipv4:

Configure IPv4 addresses
~~~~~~~~~~~~~~~~~~~~~~~~

IPv4 addresses identify your system on the network.
Set them manually as a static address, or let DHCP assign one automatically.
You write IPv4 addresses using a 32-bit length in four decimal blocks, such as ``192.0.2.10``.

For a static IP address configuration,
enter the IP address in the field *IPv4 address*
and the network mask for the network card in the field *Netmask*.
To request an address from a DHCP server, click :guilabel:`DHCP query`
and Nubus for UCS stores the IP address received from the DHCP server as static configuration.

You can also configure Nubus for UCS systems through DHCP
by activating the *Dynamic (DHCP)* option.
Nubus for UCS uses the dynamic configuration from the DHCP server.
Some cloud providers require DHCP-based server configuration.
If the DHCP server doesn't assign an IP address,
Nubus for UCS assigns a random link-local address :samp:`169.254.{x}.{y}` instead.

Nubus for UCS systems also write the DHCP-assigned address to the LDAP directory.

.. note::

   Not all services are suitable for use on a DHCP-based server.
   DNS servers, mail servers, and other services
   that clients expect to reach at consistent addresses require static IP configuration.
   Dynamic addresses can change, breaking client connections to these services.

Alternatively, you can set IPv4 addresses through :term:`UCR variables <UCR variable>`:

* :envvar:`interfaces/*/address`
* :envvar:`interfaces/*/netmask`
* :envvar:`interfaces/*/type`

For the gateway setting, see :ref:`system-administration-network-gateway`.

Besides the physical interfaces,
you can also define additional virtual interfaces in the form :envvar:`interfaces/*/setting`.
Virtual interfaces use the naming convention ``eth0_1``, ``eth0_2``, and so on.
The number in the name identifies the virtual interface.
In the network interface listing,
these appear with colons instead of underscores, such as ``eth0:1`` and ``eth0:2``.
This allows one network card to have multiple independent configurations and IP addresses.

For redundancy and load distribution across multiple network cards,
see :ref:`system-administration-network-bonding`.

.. _system-administration-network-ipv6:

Configure IPv6 addresses
~~~~~~~~~~~~~~~~~~~~~~~~

You can configure the IPv6 address in two ways:

Automatic (SLAAC)
   The routers on your network assign the IP address.
   Activate :guilabel:`Autoconfiguration (SLAAC)` in the user interface.

Static
   Enter the *IPv6 address* and *IPv6 prefix* manually in the respective fields.

You write IPv6 addresses using a 128-bit length in hexadecimal form, such as ``2001:0DB8:FE29:DE27:0000:0000:0000:0000``.

IPv6 automatic configuration (SLAAC) assigns only the IP address, not DNS server information.
Nubus for UCS doesn't run a dedicated DHCPv6 client,
but accepts DNS server information from DHCP if the server provides it.

One network card can have multiple IPv6 addresses.
Each address needs a unique *Identifier* in the respective field.
The primary address uses the *Identifier* ``default``.
Other addresses can have functional names like ``mail`` or ``web``.
For the gateway setting, see :ref:`system-administration-network-gateway`.
For network isolation using VLANs,
see :ref:`system-administration-network-vlan`.

Alternatively, you can set IPv6 addresses through :term:`UCR variables <UCR variable>`:

* :envvar:`interfaces/*/ipv6/address`
* :envvar:`interfaces/*/ipv6/prefix`
* :envvar:`interfaces/*/ipv6/acceptRA`

.. _system-administration-network-gateway:

Configure gateways
~~~~~~~~~~~~~~~~~~

In the *Global network settings* section,
enter IP addresses for the network gateway in the *Gateway (IPv4)* and *Gateway (IPv6)* fields.

IPv4 gateway
    You need a gateway to send traffic to networks outside your local subnet.

IPv6 gateway
    You can configure an IPv6 gateway, though it's optional.
    A configured gateway helps maintain consistent routing behavior.

A manually configured gateway takes priority over router advertisements (RA).
Your system uses the gateway you set, not automatic updates.
This is especially important for IPv6, where systems normally accept RA updates.

Alternatively, you can set gateways through :term:`UCR variables <UCR variable>`:

* :envvar:`gateway`
* :envvar:`ipv6/gateway`

For additional network features, see:

* :ref:`system-administration-network-vlan` for network isolation and security.
* :ref:`system-administration-network-bonding` for redundancy and failover.
* :ref:`system-administration-network-bridge` for virtualization networking.

.. _system-administration-network-name-servers:

Define name servers
~~~~~~~~~~~~~~~~~~~

There are two types of DNS servers:

External DNS Server
     Use external DNS servers to look up domain names outside your network, such as ``example.com``.
     Your internet provider usually supplies these servers.

Domain DNS Server
     A domain DNS server is the local DNS server for your Nubus for UCS domain.
     It looks up domain names and IP addresses for systems in your domain.
     When a query doesn't match a domain name in your LDAP directory,
     the domain DNS server forwards it to an external DNS server.
     All domain DNS servers in your Nubus for UCS domain return the same information
     because they query the same LDAP directory.

Nubus for UCS has three directory node types: :term:`Primary Directory Node`, :term:`Backup Directory Node`, and :term:`Replica Directory Node`.
Each runs a local DNS server for your domain.

To configure name resolution,
enter the IP address of your domain's DNS server
in the *Domain DNS Server* field.
For the primary domain DNS server,
use the address of your Primary Directory Node.

Alternatively, you can set name servers through :term:`UCR variables <UCR variable>`:

* :envvar:`nameserver1` to :envvar:`nameserver3`
* :envvar:`dns/forwarder1` to :envvar:`dns/forwarder3`

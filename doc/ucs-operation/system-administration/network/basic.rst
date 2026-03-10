.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network-basic:

Basic network configuration
---------------------------

Basic network configuration covers the fundamental tasks
for connecting your Nubus for UCS system to a network.
You configure IPv4 and/or IPv6 addresses, and set up name servers for DNS resolution.
These settings apply to standard network interfaces,
such as eth0, eth1, and are the foundation for all network communication.

.. _system-administration-network-ipv4:

Configure IPv4 addresses
~~~~~~~~~~~~~~~~~~~~~~~~

If the *Dynamic (DHCP)* option was not chosen, the IP address to be bound to the
network card must be entered. In addition to the *IPv4 address* the *net mask*
must also be entered. *DHCP query* is used to request an address from a DHCP
server. Unless the *Dynamic (DHCP)* option is activated, the values received
from the DHCP request are configured statically.

Server systems can also be configured via DHCP. This is necessary for some cloud
providers, for example. If the assignment of an IP address for a server fails, a
random link local address (:samp:`169.254.{x}.{y}`) is configured as a
replacement.

For UCS server systems the address received via DHCP is also written to the LDAP
directory.

.. note::

   Not all services (e.g., DNS servers) are suitable for use on a DHCP-based
   server.

UCR variables:

* :envvar:`interfaces/ethX/address`
* :envvar:`interfaces/ethX/netmask`
* :envvar:`interfaces/ethX/type`
* :envvar:`gateway`

Besides the physical interfaces, additional virtual interfaces can also be
defined in the form :envvar:`interfaces/ethX_Y/setting`.

.. _system-administration-network-ipv6:

Configure IPv6 addresses
~~~~~~~~~~~~~~~~~~~~~~~~

The IPv6 address can be configured in two ways: Stateless address
autoconfiguration (SLAAC) is employed in the :guilabel:`Autoconfiguration
(SLAAC)` configuration. In this, the IP address is assigned from the routers of
the local network segment. Alternatively, the address can also be configured
statically by entering the *IPv6 address* and *IPv6 prefix*.

In contrast to DHCP, in SLAAC there is no assignment of additional data such as
the DNS server to be used. There is an additional protocol for this (DHCPv6),
which, however, is not employed in the dynamic assignment. One network card can
be used for different IPv6 addresses. The *Identifier* is a unique name for
individual addresses. The main address always uses the identifier ``default``;
functional identifiers such as ``Interface mail server`` can be assigned for all
other addresses.

UCR variables:

* :envvar:`interfaces/ethX/ipv6/address`
* :envvar:`interfaces/ethX/ipv6/prefix`,
* :envvar:`interfaces/ethX/ipv6/acceptRA` activates SLAAC

Further network settings can be performed under :guilabel:`Global network
settings`.

The IP addresses for the standard gateways in the subnetwork can be entered
under *Gateway (IPv4)* and *Gateway (IPv6)*. It is not obligatory to enter a
gateway for IPv6, but recommended. A gateway configured here has preference over
router advertisements, which might otherwise be able to change the route.

UCR variables:

* :envvar:`ipv6/gateway`

.. _system-administration-network-name-servers:

Configure name servers
~~~~~~~~~~~~~~~~~~~~~~

There are two types of DNS servers:

External DNS Server
   An *External DNS Server* is employed for the resolution of host names and
   addresses outside of the UCS domain, e.g., ``univention.de``. This is
   typically a name server operated by the internet provider.

Domain DNS Server
   A *Domain DNS Server* is a local name server in the UCS domain. This name
   server usually administrates host names and IP addresses belonging to the UCS
   domain. If an address is not found in the local inventory, an external DNS
   server is automatically requested. The DNS data are saved in the LDAP
   directory service, i.e., all domain DNS servers deliver identical data.

A local DNS server is set up on the :term:`Primary Directory Node`, :term:`Backup Directory Node` and
:term:`Replica Directory Node` system roles. Here, you can configure which server should be
primarily used for the name resolution by entering the *Domain DNS
Server*.

UCR variables:

* :envvar:`nameserver1` to :envvar:`nameserver3`
* :envvar:`dns/forwarder1` to :envvar:`dns/forwarder3`,

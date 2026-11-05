.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-dhcp:

DHCP
====

The Dynamic Host Configuration Protocol (DHCP) assigns computers an IP address,
the subnet mask and further settings for the gateway or NetBIOS server as
necessary. The IP address can be set fixed or dynamic.

The use of DHCP allows central assignment and control of IP addresses via the
LDAP directory without performing manual configuration on the individual
computer systems.

The DHCP integration in UCS only supports IPv4.

In a *DHCP service*, DHCP servers are grouped in a shared LDAP configuration.
Global configuration parameters are entered in the DHCP service; specific
parameters in the subordinate objects.

A DHCP server can be installed from the Univention App Center with the
application :program:`DHCP server`. Alternatively, the software package
:program:`univention-dhcp` can be installed. Additional information can be
found in :ref:`computers-softwaremanagement-install-software`.

Every DHCP assigns IP addresses via DHCP. In the default setting, only static IP
addresses are assigned to computer objects registered in the UCS LDAP.

If only fixed IP addresses are assigned, as many DHCP servers as required may be
used in a DHCP service. All the DHCP servers procure identical data from the
LDAP and offer the DHCP clients the data multiple times. DHCP clients then
accept the first answer and ignore the rest.

If dynamic IP addresses are also assigned, the DHCP failover mechanism must be
employed and a maximum of two DHCP servers can be used per subnet.

A *DHCP host* entry is used to make the DHCP service aware of a computer. A DHCP
host object is required for computers attempting to retrieve a fixed IP address
over DHCP. DHCP computer objects do not normally need to be created manually,
because they are created automatically when a DHCP service is assigned to a
computer object with a fixed IP address.

A *DHCP subnet* entry is required for every subnet, irrespective of whether
dynamic IP addresses are to be assigned from this subnet.

Configuration parameters can be assigned to the different IP ranges by creating
*DHCP pools* within subnets. In this way unknown computers can be allowed in one
IP range and excluded from another IP range. DHCP pools can only be created
below DHCP subnet objects.

If several IP subnets are used in a physical Ethernet network, this should be
entered as a *DHCP shared subnet* below a *DHCP shared network*. *DHCP shared
subnet* objects can only be created below *DHCP shared network* objects.

Values which are set on a DHCP configuration level always apply for this level
and all subordinate levels, unless other values are specified there. Similar to
policies, the value which is closest to the object always applies.

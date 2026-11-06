.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-dhcp:

DHCP
====

The Dynamic Host Configuration Protocol (DHCP) assigns computers an IP address,
a subnet mask, and, as necessary, settings for the gateway or NetBIOS server.
The IP address can be static or dynamic.

You can use DHCP to assign and control IP addresses centrally through the LDAP directory.
You don't need to configure each computer manually.

The DHCP integration in Nubus for UCS only supports IPv4.

A *DHCP service* groups DHCP servers in a shared LDAP configuration.
You enter global configuration parameters in the DHCP service
and specific parameters in the subordinate objects.
For more information,
see :external+uv-nubus-manual:ref:`nubus-domain-dhcp-services`.

You can install a DHCP server from the Univention App Center
with the :program:`DHCP server` application.
Alternatively, you can install the :program:`univention-dhcp` software package.
For more information, see :ref:`lifecycle-package-installation-management`
in :cite:t:`uv-nubus-manual`.

Every DHCP server assigns IP addresses through DHCP.
By default, DHCP servers assign only static IP addresses
to computer objects registered in the Nubus for UCS LDAP.
For more information about DHCP server entries,
see :external+uv-nubus-manual:ref:`nubus-domain-dhcp-servers`
in :cite:t:`uv-nubus-manual`.

If you assign only static IP addresses,
you can use as many DHCP servers as required in a DHCP service.
All DHCP servers obtain identical data from LDAP,
and each server offers the data to DHCP clients.
The clients then accept the first response and ignore the rest.

If you also assign dynamic IP addresses,
you must use the DHCP failover mechanism
and can use a maximum of two DHCP servers per subnet.

A *DHCP host* entry makes a computer known to the DHCP service.
Computers need a DHCP host object
to retrieve a fixed IP address through DHCP.
You don't normally need to create DHCP host objects manually,
because Nubus creates them automatically when you assign a DHCP service
to a computer object with a fixed IP address.
For more information about DHCP host entries,
see :external+uv-nubus-manual:ref:`nubus-domain-dhcp-hosts`
in :cite:t:`uv-nubus-manual`.

Every subnet requires a *DHCP subnet* entry,
regardless of whether you assign dynamic IP addresses from that subnet.
For more information about DHCP subnet entries,
see :external+uv-nubus-manual:ref:`nubus-domain-dhcp-subnets`
in :cite:t:`uv-nubus-manual`.

You can assign configuration parameters to different IP ranges
by creating *DHCP pools* within subnets.
This lets you allow unknown computers in one IP range and exclude them from another.
You can create DHCP pools only under DHCP subnet objects.
For more information about DHCP pools,
see :external+uv-nubus-manual:ref:`nubus-domain-dhcp-pools`
in :cite:t:`uv-nubus-manual`.

If several IP subnets use the same physical Ethernet network,
create a *DHCP shared network* object under the DHCP service.
Then create a separate *DHCP shared subnet* object for each subnet
under that shared network object.
For more information about DHCP shared networks and subnets,
see :external+uv-nubus-manual:ref:`nubus-domain-dhcp-shared-network`
in :cite:t:`uv-nubus-manual`.

Values that you set at a DHCP configuration level apply to that level
and all subordinate levels unless you specify other values at those levels.
As with policies, the value closest to the object in the configuration hierarchy applies.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-dhcp`
      in :cite:t:`uv-nubus-manual`
      for information about how to use the *DHCP* management module
      in the *Management UI*.

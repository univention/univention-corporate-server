.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-dns:

DNS
===

Nubus for UCS integrates BIND for name resolution through the domain name system (DNS).
The DNS server provides name resolution for the local network.
BIND is available on all Nubus for UCS Directory Node roles.
Nubus for UCS doesn't support the installation of BIND on other system roles.

For information about configuring the name servers
that a Nubus for UCS system uses,
see :ref:`system-administration-network`.

.. _domain-infrastructure-dns-zones:

DNS zones
---------

DNS zones organize authoritative DNS data.
Each DNS zone has a primary name server that provides the original zone data.
Secondary name servers can obtain zone data through zone transfers.
An *SOA record* marks the start of a zone of authority
and contains parameters for managing the zone.

.. _domain-infrastructure-dns-forward:

Forward lookup zone
   A *forward lookup zone* contains information
   for resolving DNS names into IP addresses.

.. _domain-infrastructure-dns-reverse:

Reverse lookup zone
   A *reverse lookup zone* contains information
   for resolving IP addresses into DNS names.

.. seealso::

   For the management modules for DNS zones, see the following
   in :cite:t:`uv-nubus-manual`:

   * :external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone`
   * :external+uv-nubus-manual:ref:`nubus-domain-dns-reversezone`

.. _domain-infrastructure-dns-records:

DNS records
-----------

DNS records contain information about DNS names.
For information about how to manage DNS records,
see :external+uv-nubus-manual:ref:`nubus-domain-dns`
in :cite:t:`uv-nubus-manual`.

.. _domain-infrastructure-dns-record-mx:

MX record
   The *MX record* of a forward lookup zone provides DNS information
   for email routing.
   It points to the computer that accepts email for a domain.

.. _domain-infrastructure-dns-record-cname:

CNAME record
   A *CNAME record*, also called an alias record, refers to an existing,
   canonical DNS name.
   For example, you can create an alias entry ``mailserver``
   for the actual hostname of a mail server
   and enter the alias in mail clients.
   Any number of CNAME records can map to one canonical name.

.. _domain-infrastructure-dns-record-a:

A and AAAA records
   An *A record* assigns an IPv4 address to a DNS name.
   An *AAAA record* assigns an IPv6 address to a DNS name.
   In Nubus for UCS, a *host record* can contain IPv4 and IPv6 addresses.

.. _domain-infrastructure-dns-record-ptr:

PTR record
   A *PTR record* (pointer record) resolves an IP address into a hostname.
   In a reverse lookup zone, it's the equivalent
   of a host record in a forward lookup zone.

.. _domain-infrastructure-dns-record-srv:

SRV record
   An *SRV record*, called a service record in Nubus for UCS,
   stores information about available system services in DNS.
   In Nubus for UCS, service records make LDAP servers
   or the :term:`Primary Directory Node` known domain-wide, among other uses.

.. _domain-infrastructure-dns-record-txt:

TXT records
   *TXT records* include human-readable text and can include descriptive
   information about a forward lookup zone.

.. seealso::

   For the management modules for DNS records, see the following
   in :cite:t:`uv-nubus-manual`:

   * :external+uv-nubus-manual:ref:`nubus-domain-dns-records-alias`
   * :external+uv-nubus-manual:ref:`nubus-domain-dns-records-host`
   * :external+uv-nubus-manual:ref:`nubus-domain-dns-records-service`
   * :external+uv-nubus-manual:ref:`nubus-domain-dns-records-pointer`
   * :external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-mx-records-tab`
   * :external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-txt-records-tab`

.. _domain-infrastructure-dns-bind-configuration:

Configuration of the BIND name server
-------------------------------------

The following sections describe how to configure BIND debug output,
the data backend, and zone transfers.

.. _domain-infrastructure-dns-bind-debug:

Configuration of BIND debug output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the :term:`UCR variables <UCR variable>` :envvar:`dns/debug/level`
and :envvar:`dns/dlz/debug/level`
to configure the level of detail in BIND debug output.
The latter applies to the :ref:`domain-infrastructure-dns-data-backend-configuration-samba`.
Possible values range from ``0`` to ``11``.
Level ``0`` deactivates debug output.
Higher BIND debug levels provide more detailed output.
For information about BIND debug logging, see
`The channel phrase <https://bind9.readthedocs.io/en/v9.18.33/reference.html#the-channel-phrase>`_
in :cite:t:`bind9-admin-reference`.

For information about setting and checking a UCR variable,
see :ref:`system-administration-ucr-command-line-set`.
After changing either debug variable,
restart the BIND service as ``root`` user,
as shown in :numref:`domain-infrastructure-dns-bind-debug-listing`.

.. code-block:: console
   :caption: Restart BIND after changing the debug level
   :name: domain-infrastructure-dns-bind-debug-listing

   $ systemctl restart named

.. _domain-infrastructure-dns-data-backend-configuration:

Configuration of the data backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a typical BIND installation on a non-Nubus for UCS system,
you configure BIND by editing zone files.
In Nubus for UCS, you manage DNS zones and records through management modules.
These modules store the DNS data in the LDAP directory.

BIND can use two different backends for its configuration:

.. _domain-infrastructure-dns-data-backend-configuration-ldap:

LDAP backend
   The *LDAP backend* is the standard backend
   and accesses data in the LDAP directory.
   With this backend, the DNS service uses two servers.
   The *BIND proxy* uses the standard DNS port ``53``.
   A second server runs in the background on port ``7777``
   and obtains zone data from LDAP.
   The BIND proxy acts as a secondary server
   and obtains zone data from the second server through zone transfers.

.. _domain-infrastructure-dns-data-backend-configuration-samba:

Samba backend
   Samba/AD provides an Active Directory domain.
   Active Directory relies on DNS for purposes such as DNS updates
   from Windows clients and the discovery of NETLOGON shares.
   With the *Samba backend*,
   Samba directly updates the DNS data in its internal LDB database.
   BIND then accesses the Samba DNS data
   through its *Dynamically Loadable Zones* (DLZ) interface.

With the Samba backend, each DNS request triggers an LDAP search.
With the LDAP backend, a directory service search occurs
only if the DNS data has changed.
The LDAP backend can therefore reduce the system load on Samba/AD systems.

The :term:`UCR variable` :envvar:`dns/backend` selects the DNS backend.
The value ``ldap`` selects the LDAP backend,
and ``samba4`` selects the Samba backend.
On Directory Nodes running Samba 4, don't set the backend to ``ldap``.

You use management modules to administer DNS with either backend.

.. _domain-infrastructure-dns-zone-transfer-configuration:

Configuration of zone transfers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the Nubus for UCS name server allows zone transfers of DNS data.
If the Nubus for UCS system is reachable from the internet, anyone can request
a list of all computer names and IP addresses.

Depending on the configured data backend, the method to restrict zone transfers differs:

.. tab-set::

   .. tab-item:: LDAP backend
      :sync: ldap

      If you use the LDAP backend, you can deactivate zone transfers or restrict them
      by setting the :term:`UCR variable` :envvar:`dns/allow/transfer` to ``none``
      or a list of allowed IP addresses.

      After changing the variable, restart the BIND service as ``root``,
      as shown in :numref:`domain-infrastructure-dns-bind-debug-listing`.

   .. tab-item:: Samba backend
      :sync: samba

      .. important::

         For the Samba backend (Samba DLZ), the :envvar:`dns/allow/transfer` variable
         and standard BIND ``allow-transfer`` options are not enough to control
         zone transfers.

         For more information about this limitation and its current status,
         see :uv:bug:`55047`.

To verify whether the server allows or denies zone transfers,
use the :command:`dig` command from a client machine, as shown in :numref:`domain-infrastructure-dns-transfer-verification-listing`.
Replace the following:

* :samp:`{SERVER_IP}` with the IP address of the name server, for example ``192.168.1.1``.
* :samp:`{DOMAIN_NAME}` with the name of the zone, for example ``domain.lan``.

If the server allows the transfer, it returns the full list of zone records.
If the server denies the transfer, the output shows a ``Transfer failed``
or ``REFUSED`` message.

.. code-block:: console
   :caption: Verify DNS zone transfer
   :name: domain-infrastructure-dns-transfer-verification-listing

   $ dig @SERVER_IP DOMAIN_NAME axfr

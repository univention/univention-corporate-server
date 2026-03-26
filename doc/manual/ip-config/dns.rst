.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _networks-dns:

Administration of DNS data with BIND
====================================

UCS integrates BIND for the name resolution via the domain name system (DNS).
The majority of DNS functions are used for DNS resolution in the local domain;
however, the UCS BIND integration can also be used for a public name server in
principle.

BIND is always available on all UCS Directory Node roles; installation on other
system roles is not supported.

The configuration of the name servers to be used by a UCS system is documented
in :ref:`hardware-network-configuration`.

The following DNS data are differentiated:

Forward lookup zone
   A *forward lookup zone* contains information which is used to resolve DNS
   names into IP addresses. Each DNS zone has at least one authoritative,
   primary name server whose information governs the zone. Subordinate servers
   synchronize themselves with the authoritative server via zone transfers. The
   entry which defines such a zone is called a *SOA record* in DNS terminology.

MX record
   The *MX record* of a forward lookup zone represents important DNS information
   necessary for email routing. It points to the computer which accepts emails
   for a domain.

TXT records
   *TXT records* include human-readable text and can include descriptive
   information about a forward lookup zone.

CNAME record
   A *CNAME record*, also called an alias record, refers to an existing,
   canonical DNS name. For example, the actual hostname of the mail server can
   be given an alias entry *mailserver*, which is then entered in the mail
   clients. Any number of CNAME records can be mapped to one canonical name.

A record
   An *A record* (under IPv6 *AAAA record*) assigns an IP address to a DNS name.
   *A records* are also known as *Host records* in UCS.

SRV record
   A *SRV record*, called a service record in UCS, can be used to save
   information about available system services in the DNS. In UCS, service
   records are used among other things to make LDAP servers or the
   |UCSPRIMARYDN| known domain-wide.

Reverse lookup zone
   A *reverse lookup zone* contains information which is used to resolve IP
   addresses into DNS names. Each DNS zone has at least one authoritative,
   primary name server whose information governs the zone, subordinate servers
   synchronize themselves with the authoritative server via zone transfers. The
   entry which defines such a zone is the *SOA record*.

PTR record
   A *PTR record* (pointer record) allows resolution of an IP address into a
   hostname. It thus represents the equivalent in a reverse lookup zone of a
   host record in a forward lookup zone.

.. _ip-config-configuration-of-the-bind-nameserver:

Configuration of the BIND name server
-------------------------------------

.. _ip-config-bind-debug:

Configuration of BIND debug output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The level of detail of the BIND debug output can be configured via the
:envvar:`dns/debug/level` and :envvar:`dns/dlz/debug/level` (for the Samba
backend, see :ref:`ip-config-dns-backend`) |UCSUCR| variables. The possible
values are between ``0`` (no debug tasks) to ``11``. A complete list of levels
can be found at :cite:t:`bind-loglevel`.

.. _ip-config-dns-backend:

Configuration of the data backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a typical BIND installation on a non-UCS system, the configuration is
performed by editing zone files. In UCS, BIND is completely configured via UMC
modules, which saves its data in the LDAP directory.

BIND can use two different backend for its configuration:

LDAP backend
   The *LDAP backend* accesses the data in the LDAP directory. This is the
   standard backend. The DNS service is split into two in this case: The *BIND
   proxy* is the primary name server and uses the DNS standard port ``53``. A
   second server in the background works on port ``7777``. If data from the
   internal DNS zones are edited in the LDAP, the zone file on the second server
   is updated based on the LDAP information and transmitted to the BIND proxy by
   means of a zone transfer.

Samba backend
   Samba/AD provides an Active Directory domain. Active Directory is closely
   connected with DNS, for DNS updates of Windows clients or the localization of
   NETLOGON shares among other things. If Samba/AD is used, the UCS Directory
   Node in question is switched over to the use of the *Samba backend*. The DNS
   database is maintained in Samba's internal LDB database, which Samba updates
   directly. BIND then accesses the Samba DNS data via the DLZ interface.

When using the Samba backend, a search is performed in the LDAP for every DNS
request. With the OpenLDAP backend, a search is only performed in the directory
service if the DNS data has changed. The use of the LDAP backend can thus result
in a reduction of the system load on Samba/AD systems.

The backend is configured via the |UCSUCRV| :envvar:`dns/backend`. The DNS
administration is not changed by the backend used and is performed via UMC
modules in both cases.

.. _ip-config-configuration-of-zone-transfers:

Configuration of zone transfers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default the UCS name server allows zone transfers of the DNS data. If the UCS
server can be reached from the internet, a list of all computer names and IP
addresses can be requested. The zone transfer can be deactivated when using the
OpenLDAP backend by setting the |UCSUCRV| :envvar:`dns/allow/transfer` to
``none``.

.. _ip-config-dns-umc:

Administration of DNS data via |UCSUMC| module
----------------------------------------------

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-forwardzone:

Forward lookup zone
~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-forwardzone-general-tab:

DNS UMC module forward lookup - General tab
"""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-general-tab`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-forwardzone-start-of-authority-tab:

DNS UMC module forward lookup - Start of authority tab
""""""""""""""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-soa-tab`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-forwardzone-ip-addresses-tab:

DNS UMC module forward lookup - IP addresses tab
""""""""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-ip-addresses-tab`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-forwardzone-mx-records-tab:

DNS UMC module forward lookup - MX records tab
""""""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-mx-records-tab`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-forwardzone-txt-records-tab:

DNS UMC module forward lookup - TXT records tab
"""""""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-forwardzone-txt-records-tab`
in :cite:t:`uv-nubus-manual`.

.. _ip-config-cname-record-alias-records:

CNAME record (Alias records)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-records-alias`
in :cite:t:`uv-nubus-manual`.

.. _networks-dns-hostrecord:

A/AAAA records (host records)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-records-host`
in :cite:t:`uv-nubus-manual`.

.. _ip-config-service-records:

Service records
~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-records-service`
in :cite:t:`uv-nubus-manual`.

.. _ip-config-reverse-lookup-zone:

Reverse lookup zone
~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-reversezone`
in :cite:t:`uv-nubus-manual`.

.. _ip-config-reverse-lookup-zone-general-tab:

DNS UMC module reverse lookup - General tab
"""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-reversezone-general-tab`
in :cite:t:`uv-nubus-manual`.

.. _ip-config-reverse-lookup-zone-start-of-authority-tab:

DNS UMC module reverse lookup - Start of authority tab
""""""""""""""""""""""""""""""""""""""""""""""""""""""

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-reversezone-soa-tab`
in :cite:t:`uv-nubus-manual`.

.. _ip-config-pointer-record:

Pointer record
~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-nubus-manual:ref:`nubus-domain-dns-records-pointer`
in :cite:t:`uv-nubus-manual`.

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
   canonical DNS name. For example, the actual host name of the mail server can
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
   host name. It thus represents the equivalent in a reverse lookup zone of a
   host record in a forward lookup zone.

.. _ip-config-configuration-of-the-bind-nameserver:

Configuration of the BIND name server
-------------------------------------

.. _ip-config-bind-debug:

Configuration of BIND debug output
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The level of detail of the BIND debug output can be configured via the
:envvar:`dns/debug/level` and :envvar:`dns/dlz/debug/level` (for the Samba
backend, see :ref:`ip-config-dns-backend`) |UCSUCR| variables. The possible
values are between ``0`` (no debug tasks) to ``11``. A complete list of levels
can be found at `Reading Bind Debugging Output
<https://www.diablotin.com/librairie/networking/dnsbind/ch12_01.htm>`_.

.. _ip-config-dns-backend:

Configuration of the data backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a typical BIND installation on a non-UCS system, the configuration is
performed by editing zone files. In UCS, BIND is completely configured via UMC
modules, which saves its data in the LDAP directory.

BIND can use two different backends for its configuration:

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default the UCS name server allows zone transfers of the DNS data. If the UCS
server can be reached from the Internet, a list of all computer names and IP
addresses can be requested. The zone transfer can be deactivated when using the
OpenLDAP backend by setting the |UCSUCRV| :envvar:`dns/allow/transfer` to
``none``.

.. _ip-config-dns-umc:

Administration of DNS data via |UCSUMC| module
----------------------------------------------

DNS files are stored in the :samp:`cn=dns,{base DN}` container as standard.
Forward and reverse lookup zones are stored directly in the container.
Additional DNS objects such as pointer records can be stored in the respective
zones.

The relative or fully qualified domain name (FQDN) should always be used in the
input fields for computers and not the computer's IP address. A FQDN should
always end in a full stop to avoid the domain name being added anew.

The left column of the UMC module :guilabel:`DNS` includes a list of all the
forward and reverse lookup zones. To add an object to a zone - for example an
alias record to a forward zone - the corresponding zone must be selected.
:guilabel:`Add` is then used to create the object in this zone. To create a new
forward or reverse zone, start by selecting *All DNS zones*. Clicking on
:guilabel:`Add` then creates a new zone. If an object is created within the
zone, the zone is labeled in the UMC dialogues as a *superordinate object*.

.. _networks-dns-forwardzone:

Forward lookup zone
^^^^^^^^^^^^^^^^^^^

Forward lookup zones contain information which is used to resolve DNS names into
IP addresses. They are managed in the UMC module :guilabel:`DNS` (see
:ref:`central-user-interface`). To add another forward lookup zone, select *All
DNS zones* and :menuselection:`Add --> DNS: Forward lookup zone`.

.. _net-dns-forward:

.. figure:: /images/forward-lookup-zone.*
   :alt:  Configuring a forward lookup zone in the UMC module *DNS*

   Configuring a forward lookup zone in the UMC module *DNS*

.. _networks-dns-forwardzone-general-tab:

DNS UMC module forward lookup - General tab
"""""""""""""""""""""""""""""""""""""""""""

.. _networks-dns-forwardzone-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Zone name
     - This is the complete name of the DNS domain for which the zone will be
       responsible.

       The domain name **must not** end in a full stop in zone names!

   * - Zone time to live
     - The time to live specifies how long these files may be cached by other
       DNS servers. The value is specified in seconds.
   * - Name servers
     - The fully qualified domain name with a full stop at the end of the
       relative domain name of the responsible name server. The first entry in
       the line is the primary name server for the zone.

.. _networks-dns-forwardzone-start-of-authority-tab:

DNS UMC module forward lookup - Start of authority tab
""""""""""""""""""""""""""""""""""""""""""""""""""""""

.. _networks-dns-forwardzone-start-of-authority-tab-table:

.. list-table:: *Start of authority* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Contact person
     - The e-mail address of the person responsible for administrating the zone.

   * - Serial number
     - Other DNS servers use the serial number to recognize whether zone data
       have changed. The secondary name server compares the serial number of its
       copy with that on the primary name server. If the serial number of the
       secondary is lower than that on the primary, the secondary copies the
       changed data.

       There are two commonly used patterns for this serial number:

       * Start with ``1`` and increment the serial number with each change.

       * By including the date the number can be entered in the format
         ``YYYYMMDDNN``, where

         * ``Y`` stands for year,
         * ``M`` for month,
         * ``D`` for day and
         * ``N`` for the number of the change of this day.

       If the serial number is not changed manually, it will be increased
       automatically with every change.

   * - Refresh interval
     - The time span in seconds after which the secondary name server checks
       that its copy of the zone data is up-to-date.

   * - Retry interval
     - The time span in seconds after which the secondary name server tries
       again to check that its copy of the zone data is up-to-date after a
       failed attempt to update. This time span is usually set to be less than
       the update interval, but can also be equal.

   * - Expiry interval
     - The time span in seconds after which the copy of the zone data on the
       secondary becomes invalid if it could not be checked to be up-to-date.

       For example, an expiry interval of one week means that the copy of the
       zone data becomes invalid when all requests to update in one week fail.
       In this case, it is assumed that the files are too outdated after the
       expiry interval date to be used further. The secondary name server can
       then no longer answer name resolution requests for this zone.

   * - Negative time to live
     - The negative time to live specifies in seconds how long other servers can
       cache no-such-domain (NXDOMAIN) answers. This value cannot be set to more
       than 3 hours, the default value is 3 hours.

.. _networks-dns-forwardzone-ip-addresses-tab:

DNS UMC module forward lookup - IP addresses tab
""""""""""""""""""""""""""""""""""""""""""""""""

.. _networks-dns-forwardzone-ip-addresses-tab-table:

.. list-table:: *IP addresses* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - IP addresses
     - This input field can be used to specify one or more IP addresses, which
       are output when the name of the zone is resolved. These IP addresses are
       queried by Microsoft Windows clients in AD compatible domains.

.. _networks-dns-forwardzone-mx-records-tab:

DNS UMC module forward lookup - MX records tab
""""""""""""""""""""""""""""""""""""""""""""""

.. _networks-dns-forwardzone-mx-records-tab-table:

.. list-table:: *MX records* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - Priority
     - A numerical value between 0 and 65535. If several mail servers are
       available for the MX record, an attempt will be made to engage the server
       with the lowest priority value first.

   * - Mail server
     - The mail server responsible for this domain as fully qualified domain
       name with a full stop at the end. Only canonical names and no alias names
       can be used here.

.. _networks-dns-forwardzone-txt-records-tab:

DNS UMC module forward lookup - TXT records tab
"""""""""""""""""""""""""""""""""""""""""""""""

.. _networks-dns-forwardzone-txt-records-tab-table:

.. list-table:: *TXT records* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - TXT record
     - Descriptive text for this zone. Text records must not contain umlauts or
       other special characters.

.. _ip-config-cname-record-alias-records:

CNAME record (Alias records)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CNAME records / alias records are managed in the UMC module :guilabel:`DNS` (see
:ref:`central-user-interface`). To create another record, the forward lookup
zone must be selected in the left column. :menuselection:`Add --> DNS: Alias
record` can be used to create a new record.

.. _ip-config-cname-record-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - Alias
     - The alias name as fully qualified domain name with a full stop at the end
       or as a relative domain name which should point to the canonical name.

   * - Canonical name
     - The canonical name of the computer that the alias should point to,
       entered as a fully qualified domain name with a full stop at the end or a
       relative domain name.

.. _networks-dns-hostrecord:

A/AAAA records (host records)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Host records are managed in the UMC module :guilabel:`DNS` (see
:ref:`central-user-interface`). To create another record, the forward lookup
zone must be selected in the left column. :menuselection:`Add --> DNS: Host
record` can be used to create a new record.

When adding or editing a computer object a host record can be created
automatically or edited.

.. _networks-dns-hostrecord-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Host name
     - The FQDN with a full stop at the end or the relative domain name of the
       name server.

   * - IP addresses
     - The IPv4 and/or IPv6 addresses to which the host record should refer.

   * - Zone time to live
     - The time to live specifies in seconds how long these files may be cached
       by other DNS servers.

.. _ip-config-service-records:

Service records
^^^^^^^^^^^^^^^

Service records are managed in the UMC module :guilabel:`DNS` (see
:ref:`central-user-interface`). To create another record, the forward lookup
zone must be selected in the left column. :menuselection:`Add --> DNS: Service record`
can be used to create a new record.

.. _net-srv-record:

.. figure:: /images/srv-record.*
   :alt: Configuring a service record

   Configuring a service record

A service record must always be assigned to a forward lookup zone and can
therefore only be added to a forward lookup zone or a subordinate container.

.. _ip-config-service-records-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Service
     - The name under which the service should be reachable.

   * - Protocol
     - The protocol via which the record can be accessed (``TCP``, ``UDP``,
       ``MSDCS`` or ``SITES``).

   * - Extension
     - This input field can be used to specify additional parameters.

   * - Priority
     - A whole number between 0 and 65535. If more than one server offer the
       same service, the client will approach the server with the lowest
       priority value first.

   * - Weighting
     - A whole number between 0 and 65535. The weight function is used for load
       balancing between servers with the same priority. When more than one
       server offer the same service and have the same priority the load is
       distributed across the servers in relation to the weight function.

       Example: ``Server1`` has a priority of ``1`` and a weight function of
       ``1``, whilst ``Server2`` also has a priority of ``1``, but has a weight
       function of ``3``. In this case, ``Server2`` will be used three times as
       often as ``Server1``. The load is measured depending on the service, for
       example, as the number of requests or connection.

   * - Port
     - The port where the service can be reached on the server (valid value from
       1 to 65535).

   * - Server
     - The name of the server on which the service will be made available, as a
       fully qualified domain name with a full stop at the end or a relative
       domain name.

       Several servers can be entered for each service.

   * - Zone time to live
     - The time to live specifies how long these files may be cached by other
       DNS servers.

.. _ip-config-reverse-lookup-zone:

Reverse lookup zone
^^^^^^^^^^^^^^^^^^^

A reverse lookup zone is used to resolve IP address into host names. They are
managed in the UMC module :guilabel:`DNS`. To add another reverse lookup zone,
select *All DNS zones* and :menuselection:`Add --> DNS: Reverse lookup zone`.

.. _ip-config-reverse-lookup-zone-general-tab:

DNS UMC module reverse lookup - General tab
"""""""""""""""""""""""""""""""""""""""""""

.. _ip-config-reverse-lookup-zone-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Subnet
     - The IP address of the network for which the reverse lookup zone shall
       apply. For example, if the network in question consisted of the IP
       addresses ``192.0.2.0`` to ``192.0.2.255``, ``192.0.2`` should be
       entered.

   * - Zone time to live
     - The time to live specifies how long these files may be cached by other
       DNS servers.

Each DNS zone has at least one authoritative, primary name server whose
information governs the zone. Subordinate servers synchronize themselves
with the authoritative server via zone transfers. The entry which
defines such a zone is called a SOA record in DNS terminology.

.. _ip-config-reverse-lookup-zone-start-of-authority-tab:

DNS UMC module reverse lookup - Start of authority tab
""""""""""""""""""""""""""""""""""""""""""""""""""""""

.. _ip-config-reverse-lookup-zone-start-of-authority-tab-table:

.. list-table:: *Start of authority* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Contact person
     - The e-mail address of the person responsible for administrating the zone
       (with a full stop at the end).

   * - Name servers
     - The fully qualified domain name with a full stop at the end or the
       relative domain name of the primary name server.

   * - Serial number
     - See the documentation on forward lookup zones in
       :ref:`networks-dns-forwardzone`.

   * - Refresh interval
     - See the documentation on forward lookup zones in
       :ref:`networks-dns-forwardzone`.

   * - Retry interval
     - See the documentation on forward lookup zones in
       :ref:`networks-dns-forwardzone`.

   * - Expiry interval
     - See the documentation on forward lookup zones in
       :ref:`networks-dns-forwardzone`.

   * - Minimum time to live
     - See the documentation on forward lookup zones in
       :ref:`networks-dns-forwardzone`.

.. _ip-config-pointer-record:

Pointer record
^^^^^^^^^^^^^^

Pointer records are managed in the UMC module :guilabel:`DNS` (see
:ref:`central-user-interface`). To create another record, the reverse lookup
zone must be selected in the left column. :menuselection:`Add --> DNS: Pointer
record` can be used to create a new record.

.. _ip-config-pointer-record-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 2 9

   * - Attribute
     - Description

   * - Address
     - The last octet of the computer's IP address (depends on network prefix,
       see example below).

   * - Pointer
     - The computer's fully qualified domain name with a full stop at the end.

       In a network with a 24-bit network prefix (subnet mask ``255.255.255.0``)
       a pointer should be created for the ``client001`` computer with the IP
       address ``192.0.2.101``. ``101`` must then be entered in the
       :guilabel:`Address field` and ``client001.company.com.`` in
       :guilabel:`Pointer`.

       Example:

       For a network with a 16-bit network prefix (subnet mask ``255.255.0.0``)
       the last two octets should be entered in reverse order for this computer
       (here ``101.1``). ``client001.company.com.`` also needs to be entered in
       the :guilabel:`Pointer` field here.

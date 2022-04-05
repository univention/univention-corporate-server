.. _module-dhcp-dhcp:

IP assignment via DHCP
======================

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
found in :ref:`computers-softwaremanagement-installsoftware`.

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

.. _networks-dhcp-general:

Composition of the DHCP configuration via DHCP LDAP objects
-----------------------------------------------------------

The left column of the UMC module :guilabel:`DHCP` includes a list of all the
DHCP services. To add an object to a DHCP service - for example in an additional
subnet - the corresponding service must be selected. :guilabel:`Add` is then
used to create the object in this service. To create a new DHCP service, start
by selecting *All DHCP services*. Clicking on :guilabel:`Add` then creates a new
service. If an object is saved within a service, the service is labeled in UMC
dialogues as a *superordinate object*.

.. _networks-dhcp-services:

Administration of DHCP services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DHCP services are managed in the UMC module :guilabel:`DHCP` (see
:ref:`central-user-interface`). To create a new DHCP service, *All DHCP
services* needs to be selected in the left column of the UMC module. Clicking
on :guilabel:`Add` then creates a new service.

A DHCP server can only serve one DHCP service; to use another DHCP service, a
separate DHCP server must be set up (see :ref:`networks-dhcp-dhcpserver`).

The following parameters are often set on the DHCP service object which then
apply to all the computers which are served by this DHCP service (unless other
values are entered in lower levels):

* *Domain name* and *Domain name servers* under *Policy: DHCP DNS*

* *NetBIOS name servers* under *Policy: DHCP NetBIOS*

A description of this and the other DHCP policies can be found at
:ref:`networks-dhcp-policies`.

.. _networks-dhcp-services-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - Service name
     - An unambiguous name for the DHCP service must be entered in this input
       field, e.g., ``company.example``.

.. _networks-dhcp-dhcpserver:

Administration of DHCP server entries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each server which should offer the DHCP service requires a *DHCP server* entry
in the LDAP directory. The entry does not normally need to be created manually,
instead it is created by the join script of the :program:`univention-dhcp`
package. However, to create another record manually, a DHCP service must be
selected in the left column of the UMC module :guilabel:`DHCP`.
:menuselection:`Add --> DHCP Server` can then be used to register a new server.

.. _networks-dhcp-dhcpserver-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - Server name
     - The computer name that the DHCP service should offer is entered in this
       input field, e.g., ``ucs-primary``.

       A server can only ever provide a single DHCP service and therefore cannot
       be entered in more than one DHCP service at the same time.

.. _ip-config-administration-of-dhcp-subnets:

Administration of DHCP subnets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DHCP subnets are managed in the UMC module :guilabel:`DHCP` (see
:ref:`central-user-interface`). To create another subnet, a DHCP service must be
selected in the left column. :menuselection:`Add --> DHCP: Subnet` can be used
to create a new subnet.

A DHCP subnet entry is required for every subnet from which dynamic or fixed IP
addresses are to be assigned. It is only necessary to enter IP address ranges if
IP addresses are to be assigned dynamically.

If *DHCP shared subnet* objects are to be used, the corresponding subnets should
be created below the *DHCP shared subnet* container created for this purpose
(see :ref:`networks-dhcp-sharedsubnets`).

.. _ip-config-administration-of-dhcp-subnets-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Subnet address
     - The IP address of the subnet must be entered in dot-decimal form in this
       input field, e.g., ``192.0.2.0``.

   * - Net mask
     - The network mask can be entered in this input field as the network prefix
       or in dot-decimal form. If the network mask is entered in dot-decimal
       form it will be subsequently be converted into the corresponding network
       prefix and later also shown so.

   * - Dynamic address assignment
     - Here one can set up individual or multiple IP address ranges for dynamic
       assignment. The range stretches from the *First address* to the *Last
       address* in dot-decimal form.

       .. caution::

          Dynamic IP ranges for a subnet should always either be specified
          exclusively in the subnet entry or exclusively in one or more special
          pool entries. The types of IP range entries within a subnet must not
          be mixed! If different IP ranges with different configurations are be
          set up in one subnet, pool entries must be created for this purpose.

At this level, the gateway for all computers in a subnet is often set using the
*Policy: DHCP Routing* tab (unless other entries are performed at lower levels).

.. _ip-config-administration-of-dhcp-pools:

Administration of DHCP pools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DHCP pools can only be managed via the UMC module :guilabel:`LDAP directory`. To
do so, one must always be in a DHCP subnet object - a DHCP pool object must
always be created below a DHCP subnet object - and a *DHCP: Pool* object added
with :guilabel:`Add`.

If DHCP pools are created in a subnet, no IP address range should be defined in
the subnet entry. These should only be specified via the pool entries.

.. _ip-config-administration-of-dhcp-pools-general-tab:

.. rubric:: General tab

.. _ip-config-administration-of-dhcp-pools-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name
     - An unambiguous name for the DHCP pool must be entered in this input
       field, e.g., ``testnet.compaby.example``.

   * - Dynamic range
     - Here you can enter the IP addresses in dot-decimal form that are to be
       dynamically assigned.

.. _ip-config-administration-of-dhcp-pools-advanced-settings-tab:

.. rubric:: Advanced settings tab

.. _ip-config-administration-of-dhcp-pools-advanced-settings-tab-table:

.. list-table:: *Advanced settings* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Failover peer
     - The name of a failover configuration, which must to be configured
       manually in file :file:`/etc/dhcp/local.conf`. Further information can
       be found at `A Basic Guide to Configuring DHCP Failover
       <https://kb.isc.org/docs/aa-00502>`_.

   * - Allow known clients
     - A computer is identified by its MAC address. If this input field is set
       to ``allow`` or unset, a computer **with** a matching DHCP host entry (see
       :ref:`ip-config-dhcp-objects-hosts`) is eligible to receive an IP address
       from this pool.

       If set to ``deny``, the computer doesn't receive an IP address from the
       pool.

   * - Allow unknown clients
     - A computer is identified by its MAC address. If this input field is set
       to ``allow`` or unset, a computer **without** a matching DHCP host
       entry (see :ref:`ip-config-dhcp-objects-hosts`) is eligible to receive an
       IP address from this pool.

       If set to ``deny``, the computer doesn't receive an IP address from the
       pool.

   * - Allow dynamic BOOTP clients
     - BOOTP is the predecessor of the DHCP protocol. It has no mechanism to
       renew leases and by default assigns leases infinitely, which can deplete
       the pool. If this options is set to ``allow`` clients can retrieve an IP
       address from this pool using BOOTP.

   * - All clients
     - If this option is set to ``deny`` the pool is disabled globally. This is
       only useful in exceptional scenarios.

.. _ip-config-dhcp-objects-hosts:

Registration of computers with DHCP computer objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A *DHCP host* entry is used to register the respective computer in the DHCP
service. Computers can be handled depending on their registration status. Known
computers may get fixed and dynamic IP addresses from the DHCP service; unknown
computers only get dynamic IP addresses.

DHCP computer entries are usually created automatically when a computer is added
via the computer management. Below the DHCP service object you have the
possibility of adding DHCP computer entries or editing existing entries
manually, irrespective of whether they were created manually or automatically.

DHCP host objects are managed in the UMC module :guilabel:`DHCP` (see
:ref:`central-user-interface`). To register a host in the DHCP manually, a DHCP
service must be selected in the left column of the module. :menuselection:`Add
--> DHCP: Host` can be used to register a host.

.. _ip-config-dhcp-objects-hosts-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Host name
     - A name for the computer is entered in this input field (which usually
       also has an entry in the computer management). It is recommended to enter
       the same name and the same MAC address for the computer in both entries
       to facilitate assignment.

   * - Type
     - The type of network used can be selected in this selection list.
       *Ethernet* almost always needs to be selected here.

   * - Address
     - The MAC address of the network card needs to be entered here, e.g.,
       ``2e:44:56:3f:12:32`` or ``2e-44-56-3f-12-32``.

   * - Fixed IP addresses
     - One or more fixed IP addresses can be assigned to the computer here. In
       addition to an IP address, a fully qualified domain name can also be
       entered, which is resolved into one or more IP addresses by the DHCP
       server.

.. _networks-dhcp-sharedsubnets:

Management of DHCP shared networks / DHCP shared subnets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*DHCP shared network* objects accept subnets which use a common physical
network.

DHCP shared network objects are managed in the UMC module :guilabel:`DHCP` (see
:ref:`central-user-interface`). To create a shared network, a DHCP service must
be selected in the left column of the module. :menuselection:`Add --> DHCP:
Shared Network` can be used to register a network.

.. caution::

   A shared network must contain at least one shared subnet object.
   Otherwise the DHCP service will terminate itself and cannot be
   restarted until the configuration is fixed.

.. _networks-dhcp-sharedsubnets-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Shared network name
     - A name for the shared network must be entered in this input field.

Subnets are declared as a *DHCP shared subnet* when they use the same, common
physical network. All subnets which use the same network must be stored below
the same shared network container. A separate *DHCP shared subnet* object must
be created for each subnet.

DHCP shared subnet objects can only be managed via the UMC module
:guilabel:`LDAP directory`. To do so, one must always be in a DHCP shared
network object - a DHCP shared subnet object must always be created below a DHCP
shared network object - and a *DHCP shared subnet* object added with
:guilabel:`Add`.

.. _networks-dhcp-policies:

Configuration of clients via DHCP policies
------------------------------------------

.. note::

   Many of the settings for DHCP are configured via policies. They are also
   applied to DHCP computer objects if a policy is linked to the LDAP base or
   one of the other intermediate containers. As the settings for DHCP computer
   objects have the highest priority, other settings for subnetwork and service
   objects are ignored.

   For this reason, DHCP policies should be linked directly to the DHCP network
   objects (e.g., the DHCP subnetworks).

   Alternatively, the LDAP class ``univentionDhcpHost`` can be added in the
   advanced settings of the policies under :menuselection:`Object --> Excluded
   object classes`. Such policies are then no longer applied to the DHCP
   computer objects, with the result that the settings from the DHCP subnetwork
   and service are used.

.. tip::

   When using the command line :command:`udm dhcp/host list`
   (see also :ref:`central-udm-example-dnsdhcp`), it is possible to
   use the option ``--policies 0`` to display the
   effective settings.

.. _ip-config-setting-the-gateway:

Setting the gateway
^^^^^^^^^^^^^^^^^^^

The default gateway can be specified via DHCP with a *DHCP routing* policy,
which is managed in the UMC module :guilabel:`Policies` (see
:ref:`central-policies`)

.. _ip-config-setting-the-gateway-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - Routers
     - The names or IP addresses of the routers are to be entered here. It must
       be verified that the DHCP server can resolve these names in IP addresses.
       The routers are contacted by the client in the order in which they stand
       in the selection list.

.. _ip-config-setting-the-dns-servers:

Setting the DNS servers
^^^^^^^^^^^^^^^^^^^^^^^

The name servers to be used by a client can be specified via DHCP with a *DHCP
DNS* policy, which is managed in the UMC module :guilabel:`Policies` (see
:ref:`central-policies`)

.. _ip-config-setting-the-dns-servers-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Domain name
     - The name of the domain, which the client automatically appends on
       computer names that it sends to the DNS server for resolution and which
       are not FQDNs. Usually this is the name of the domain to which the client
       belongs.

   * - Domain name servers
     - Here IP addresses or fully qualified domain names (FQDNs) of DNS servers
       can be added. When using FQDNs, it must be verified that the DHCP server
       can resolve the names in IP addresses. The DNS servers are contacted by
       the clients according to the order specified here.

.. _networks-dhcp-wins:

Setting the WINS server
^^^^^^^^^^^^^^^^^^^^^^^

The WINS server to be used can be specified via DHCP with a *DHCP NetBIOS*
policy, which is managed in the UMC module :guilabel:`Policies` (see
:ref:`central-policies`)

.. _networks-dhcp-wins-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - NetBIOS name servers
     - The names or IP addresses of the NetBIOS name servers (also known as WINS
       servers) should be entered here. It must be verified that the DHCP server
       can resolve these names in IP addresses. The servers entered are
       contacted by the client in the order in which they stand in the selection
       list.

   * - NetBIOS scope
     - The NetBIOS over TCP/IP scope for the client according to the
       specification in :rfc:`1001` and :rfc:`1002`. Attention must be paid to
       uppercase and lowercase when entering the NetBIOS scope.

   * - NetBIOS node type
     - This field sets the node type of the client. Possible values are:

       * ``1 B-node`` (Broadcast: no WINS)

       * ``2 P-node`` (Peer: only WINS)

       * ``4 M-node`` (Mixed: first Broadcast, then WINS)

       * ``8 H-node`` (Hybrid: first WINS, then Broadcast)

.. _ip-config-configuration-of-the-dhcp-lease:

Configuration of the DHCP lease
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The validity of an assigned IP address - a so-called DHCP lease - can be
specified with a *DHCP lease time* policy, which is managed in the UMC module
:guilabel:`Policies` (see :ref:`central-policies`)

.. _ip-config-configuration-of-the-dhcp-lease-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Default lease time
     - If the client does not request a specific lease time, the standard lease
       time is assigned. If this input field is left empty, the DHCP server's
       default value is used.

   * - Maximum lease time
     - The maximum lease time specifies the longest period of time for which a
       lease can be granted. If this input field is left empty, the DHCP
       server's default value is used.

   * - Minimum lease time
     - The minimum lease time specifies the shortest period of time for which a
       lease can be granted. If this input field is left empty, the DHCP
       server's default value is used.

.. _ip-config-configuration-of-boot-server-pxe-settings:

Configuration of boot server/PXE settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A *DHCP Boot* policy is used to assign computer configuration parameters for
booting via BOOTP/PXE. They are managed in the UMC module :guilabel:`Policies`
(see :ref:`central-policies`)

.. _ip-config-configuration-of-boot-server-pxe-settings-boot-tab-table:

.. list-table:: *Boot* tab
   :header-rows: 1
   :widths: 2 10

   * - Attribute
     - Description

   * - Boot server
     - The IP address or the FQDN of the PXE boot server from which the client
       should load the boot file is entered in the input field. If no value is
       entered in this input field, the client boots from the DHCP server from
       which it retrieves its IP address.

   * - Boot filename
     - The path to the boot file is entered here. The path must be entered
       relative to the base directory of the TFTP service
       (:file:`/var/lib/univention-client-boot/`).

.. _ip-config-further-dhcp-policies:

Further DHCP policies
^^^^^^^^^^^^^^^^^^^^^

There are some further DHCP policies available, but they are only required in
special cases.

DHCP Dynamic DNS
   *DHCP Dynamic DNS* allows the configuration of dynamic DNS updates. These
   cannot yet be performed with a LDAP-based DNS service as provided
   out-of-the-box by UCS.

DHCP Allow/Deny
   *DHCP Allow/Deny* allows the configuration of different DHCP options, which
   control what clients are allowed to do. The are only useful in exceptional
   cases.

DHCP statements
   *DHCP statements* allows the configuration of different options, which are
   only required in exceptional cases.

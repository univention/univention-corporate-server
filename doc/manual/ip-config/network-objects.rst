.. _network-objects:

Network objects
===============

*Network objects* can be used to compile available IP addresses; the next
available address is then automatically specified during assignment to a
computer.

.. _net-networks:

.. figure:: /images/create-network.*
   :alt: Creating a network object

   Creating a network object

For example, it is possible to define a network object *Workstation network*
which encompasses the IP addresses from ``192.0.2.0`` to ``192.0.2.254``. If a
Windows computer object is now created and only the network object selected, an
internal check is performed for which IP addresses are already assigned and the
next free one selected. This saves the administrator having to compile the
available addresses manually. If a computer object is removed, the address is
automatically reassigned.

Network objects are managed in the UMC module :guilabel:`Networks`. For more
information about UMC, see :ref:`central-user-interface`.

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description

   * - Name
     - The name of the network is entered in this input field. This is the name
       under which the network also appears in the computer management.

   * - Networks
     - The network address is entered in dot-decimal form in this input field,
       e.g., ``192.0.2.0``.

   * - Netmask
     - The network mask can be entered in this input field in network prefix or
       dot-decimal form. If the network mask is entered in dot-decimal form it
       will be subsequently be converted into the corresponding network prefix
       and later also shown so.

   * - IP address range
     - One or more IP ranges can be configured here. When a host is assigned to
       this network at a later point, it will automatically be assigned the
       next, free IP address from the IP range entered here.

       When no IP range is entered here, the system automatically uses the range
       given by the network and the subnet mark entered.

       Forward lookup zones and reverse lookup zones can be selected in the sub
       menu *DNS preferences*. When a host is assigned to this network at a
       later point, a host record in the forward lookup zone and/or a pointer
       record in the reverse lookup zone will be created automatically.

       The zones are also administrated in the UMC module :guilabel:`DNS`, see
       :ref:`networks-dns-forwardzone`.

       If no zone is selected here, no DNS records are created during
       assignment to a computer object. However, the DNS entries can still be
       set manually.

   * - DNS forward lookup zone
     - The forward lookup zone where hosts from the network should be added must
       be specified here. The resolution of the computer name to an IP address
       is performed via the zone.

   * - DNS reverse lookup zone
     - The reverse lookup zone where hosts from the network should be added must
       be specified here. The reverse resolution of the IP address back to a
       computer name is performed via the zone.

       A DHCP service can be assigned to the network in the sub menu *DHCP
       preferences*. When a host is assigned to this network at a later point, a
       DHCP computer entry with a fixed IP address will be created automatically
       in the selected DHCP service.

       The DHCP service settings are also administrated in the UMC module
       :guilabel:`DHCP`, see :ref:`networks-dhcp-general`.

       If no DHCP service is selected, no DHCP host record is created during
       assignment to a computer object. However, such an entry can also still be
       assigned manually.

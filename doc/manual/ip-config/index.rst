.. _networks-general:

*************************
IP and network management
*************************

This chapter describes how IP addresses for computer systems in a UCS domain can
be centrally managed via UMC modules and assigned via DHCP.

:ref:`network-objects` bundle available IP address segments of a network. The
DNS resolution as well as the assignment of IP addresses via DHCP are integrated
in UCS, as detailed in :ref:`networks-dns` and :ref:`module-dhcp-dhcp`.

Incoming and outgoing network traffic can be restricted via the *Univention
Firewall* based on :command:`iptables`, see
:ref:`ip-config-packet-filter-with-univention-firewall`.

The integration of the proxy server Squid allows the caching of web contents and
the enforcement of content policies for web access, see
:ref:`ip-config-web-proxy-for-caching-and-policy-management-virus-scan`.

.. toctree::

   network-objects
   dns
   dhcp
   firewall-packet-filter
   web-proxy
   radius

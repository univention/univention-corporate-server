.. _ip-config-packet-filter-with-univention-firewall:

Packet filter with Univention Firewall
======================================

Univention Firewall integrates a packet filter based on :program:`iptables` in
Univention Corporate Server.

It permits targeted filtering of undesired services and the protection of
computers during installations. Furthermore it provides the basis for complex
scenarios such as firewalls and application level gateways. Univention Firewall
is included in all UCS installations as standard.

By default all incoming ports are blocked. Every UCS package provides rules,
which free up the ports required by the package again.

The configuration is primarily performed via |UCSUCR| variables. The definition
of this type of packet filter rules is documented in `Univention Developer
Reference <https://docs.software-univention.de/developer-reference-5.0.html>`_.

In addition, the configuration scripts in the
:file:`/etc/security/packetfilter.d/` directory are listed in alphabetic order.
The names of all scripts begin with two digits, which makes it easy to create a
numbered order. The scripts must be marked as executable.

After changing the packet filter settings, the :program:`univention-firewall`
service has to be restarted.

Univention Firewall can be deactivated by setting the |UCSUCRV|
:envvar:`security/packetfilter/disabled` to ``true``

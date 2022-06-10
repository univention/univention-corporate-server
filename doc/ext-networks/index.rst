.. _entry-point:

##############################################################################
Univention Corporate Server - Extended IP and network management documentation
##############################################################################

.. contents::

.. _proxy:

****************************
Advanced proxy configuration
****************************

.. _proxy-cascading:

Cascading of proxies
====================

In some scenarios, cascading of proxy servers may be required. In such a setup,
individual proxy servers access logically superordinate proxy servers when web
sites are opened, which then fetch the requested data from the internet. This
allows creation of a hierarchical structure of proxy servers and, for example,
the operation of a central cache in a company's headquarters that the proxy
servers at the individual company sites can access.

The superordinate proxy server is referred to as a *parent proxy*. The parent
proxy can be specified via the |UCSUCR| variables :envvar:`squid/parent/host`
(IP address or hostname) and :envvar:`squid/parent/port` (port number).

Proxy requests from computers in the proxy server's local network are answered
directly and not forwarded to the parent proxy. If additional networks should be
excluded from forwarding to the parent proxy, these can be specified via the
|UCSUCRV| :envvar:`squid/parent/directnetworks`. When doing so, the CIDR
notation must be used (e.g. ``192.0.2.0``/``24``); several networks should be
separated by blank spaces.

.. _proxy-transparent:

Operation as a transparent proxy
================================

It is possible to configure Squid as a transparent proxy. This can help avoid
configuring the proxy server in all application programs. When using a
transparent proxy, all unencrypted web queries are automatically rerouted
through the proxy server.

.. note::

   This only works for unencrypted web traffic, not for ``https``.

.. note::

   LDAP authentication on the proxy server must not be enabled.

The following configuration steps need to be made:

* The proxy server must be configured as the default gateway on all clients.

* The proxy server must be configured to use IP forwarding.

  .. code-block:: console

     $ echo "net.ipv4.ip_forward = 1" >/etc/sysctl.d/ip_forward.conf
     $ sysctl --system


* The |UCSUCRV| :envvar:`squid/transparentproxy` must be set to ``yes`` on the
  proxy server. After that Univention Firewall and Squid need to be restarted:

  .. code-block:: console

     $ systemctl restart univention-firewall squid

  This enables packet filter rules which redirect all queries for the web ports
  to the proxy server.


.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _entry-point:

##############################################################################
Univention Corporate Server - Extended IP and network management documentation
##############################################################################

.. _proxy:

****************************
Advanced proxy configuration
****************************

This section describes some scenarios for using the web proxy.

For information about the installation of the proxy server,
see :external+uv-manual:ref:`ip-config-installation`.

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

It's possible to configure Squid as a transparent proxy.
This can help to avoid the configuration of the proxy server in all application programs.
When using a transparent proxy,
all unencrypted web queries are automatically rerouted through the proxy server.

.. important::

   The transparent proxy only works for unencrypted web traffic through HTTP,
   and not for HTTPS.

.. note::

   The transparent proxy requires that you turned off the LDAP authentication on the proxy server.
   The turned off LDAP authentication is the default setting.

To configure the transparent proxy, use the following steps:

#. Configure the proxy server as the default gateway on all clients.

#. Enable the transparent proxy by setting :envvar:`squid/transparentproxy` to
   ``true``.

#. Restart the proxy server and the firewall:

   .. code-block:: console

      $ systemctl restart univention-firewall.service squid.service

The UCS system that runs the proxy server,
redirects all incoming proxy traffic to the transparent proxy port
of the proxy server.

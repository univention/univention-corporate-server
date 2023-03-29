.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _entry-point:

##############################################################################
Univention Corporate Server - Extended IP and network management documentation
##############################################################################

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


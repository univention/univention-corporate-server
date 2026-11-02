.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-web-proxy:

Provide a web proxy service with Squid
======================================

The Nubus for UCS proxy integration uses Squid as a web cache
to improve performance and control data traffic.
It supports HTTP, FTP, and HTTPS.

A proxy server receives requests for internet content
and checks whether the requested content is available in its local cache.
It can serve cached content or retrieve content from the web server.
Caching can reduce response times and internet traffic.

For more information about proxy services,
including proxy server cascading, transparent proxies, and virus scan integration,
see :cite:t:`ext-doc-net`.

.. _system-administration-web-proxy-installation:

Installation
------------

You can install Squid from the Univention App Center
using the application :program:`Web proxy / web cache (Squid)`.
For more information about how to install an app, see :ref:`lifecycle-app-center-installation`.

Alternatively, you can install the :program:`univention-squid` software package.
For more information, see :ref:`lifecycle-package-installation-management`.

The default settings allow you to use the service immediately.
The default access port is ``3128``.
To configure a different port,
see :ref:`system-administration-web-proxy-ports-proxy`.

.. seealso::

   :ref:`lifecycle-app-center`
      for information about Univention App Center.

.. _system-administration-web-proxy-additional-configuration:

Additional configuration and restart
------------------------------------

If you change the configuration, restart Squid.
You can restart Squid through the :guilabel:`System services` management module
in the *Management UI*.
You need authorization to use the module.
For instructions, see :ref:`system-administration-service-management`.

Alternatively, restart Squid from the command line with ``root`` privileges,
as shown in :numref:`system-administration-web-proxy-additional-configuration-listing`.

.. code-block:: console
   :caption: Restart Squid
   :name: system-administration-web-proxy-additional-configuration-listing

   $ systemctl restart squid

In addition to the Univention Configuration Registry settings,
you can set Squid configuration options in the :file:`/etc/squid/local.conf` file.

.. _system-administration-web-proxy-caching-web:

Caching of web content
----------------------

Squid can serve cached content without retrieving it again from the web server.
This reduces incoming internet traffic
and can result in faster responses to HTTP requests.

Caching isn't necessary in some environments.
In a proxy cascade, you can deactivate caching on individual proxies.
To deactivate Squid caching, set the
:term:`UCR variable` :envvar:`squid/cache` to ``no``.
Then restart Squid, as shown in :numref:`system-administration-web-proxy-additional-configuration-listing`.

.. _system-administration-web-proxy-logging:

Logging proxy accesses
----------------------

The proxy server records access through it in the :file:`/var/log/squid/access.log` file.
You can use the log file to see which websites users have accessed.

.. _system-administration-web-proxy-ports:

Configuration of the ports used
-------------------------------

You can configure the port that clients use to connect to Squid
and the destination ports that Squid permits for client requests.

.. _system-administration-web-proxy-ports-proxy:

Access port
~~~~~~~~~~~

By default, you can access the web proxy through port ``3128``.
To use a different port, configure the
:term:`UCR variable` :envvar:`squid/httpport`.
Then restart Squid, as shown in
:numref:`system-administration-web-proxy-additional-configuration-listing`.

If you use Univention Firewall,
ensure that its incoming TCP rules permit the selected port
for the intended clients.
For more information, see :ref:`system-administration-network-firewall`.

.. _system-administration-web-proxy-ports-permitted:

Permitted ports
~~~~~~~~~~~~~~~

By default, Squid forwards client requests only to ports
80 (HTTP), 443 (HTTPS), or 21 (FTP).
You can change the permitted ports using the
:term:`UCR variable` :envvar:`squid/webports`.
Separate multiple entries with a single space.
Don't add spaces before the first entry or after the last entry.

:numref:`system-administration-web-proxy-permitted-ports-listing`
shows how to set the permitted ports.
Run the command with ``root`` privileges.
With this setting, the proxy allows access only to ports 80 and 443 (HTTP and HTTPS).
To apply the settings, you need to restart Squid as described in
:ref:`system-administration-web-proxy-additional-configuration`.

.. code-block:: console
   :caption: Set the permitted ports
   :name: system-administration-web-proxy-permitted-ports-listing

   $ univention-config-registry set squid/webports="80 443"

.. seealso::

   `CIDR notation - Wikipedia <https://en.wikipedia.org/w/index.php?title=Classless_Inter-Domain_Routing&oldid=1380978284>`_
      for more information about the CIDR notation.

.. _system-administration-web-proxy-restrict-to-permitted-networks:

Restriction of access to permitted networks
-------------------------------------------

By default, the proxy server can be accessed only from local networks.
For example, a computer running Squid has a network interface
with the address ``192.0.2.10`` and the network mask ``255.255.255.0``.
In this case, only computers on the network ``192.0.2.0/24``
can access the proxy server.

You can specify additional networks using the
:term:`UCR variable` :envvar:`squid/allowfrom`.
Use CIDR notation and separate multiple networks with spaces.

:numref:`system-administration-web-proxy-permitted-networks-listing`
shows how to permit access from additional networks.
Run the command with ``root`` privileges.
After you restart Squid,
the networks ``192.0.2.0/24`` and ``192.0.3.0/24`` can access the proxy.
If you set :envvar:`squid/allowfrom` to ``all``,
all networks can access the proxy.

.. code-block:: console
   :caption: Permit access from additional networks
   :name: system-administration-web-proxy-permitted-networks-listing

   $ univention-config-registry set squid/allowfrom="192.0.2.0/24 192.0.3.0/24"

.. _system-administration-web-proxy-authentication:

User authentication on the proxy
--------------------------------

You may need to restrict web access to certain users.
Squid lets you control user access based on group membership.
To verify group membership, users must authenticate with the proxy server.

.. caution::

   Proxy authentication alone doesn't prevent users
   from bypassing the proxy server and accessing the internet.
   To prevent unauthorized users from opening websites,
   you need additional measures.
   Restrict direct internet access for the traffic
   that your deployment requires users to send through the proxy,
   including HTTPS where applicable.

First, enable proxy authentication to allow verification of group membership.
There are three possible mechanisms for proxy authentication:

LDAP server authentication
   To authenticate directly with the LDAP server,
   set the :term:`UCR variable` :envvar:`squid/basicauth` to ``yes``
   and :ref:`restart Squid <system-administration-web-proxy-additional-configuration>`.

NTLM authentication
   Authentication uses the NTLM interface.
   Users signed in to a Windows client don't need to authenticate again
   when accessing the proxy.
   To enable NTLM authentication, set the UCR variable
   :envvar:`squid/ntlmauth` to ``yes``
   and :ref:`restart Squid <system-administration-web-proxy-additional-configuration>`.

Kerberos authentication
   Authentication uses Kerberos.
   Users signed in to a Windows client that is a member of a Samba/AD domain
   authenticate with the proxy using the ticket they received
   when they signed in to the domain.

   To enable Kerberos authentication,
   install the :program:`univention-squid-kerberos` package on every proxy server.
   For information about how to install a package, see :ref:`lifecycle-package-installation-management`.

   Then set the UCR variable :envvar:`squid/krb5auth` to ``yes``
   and :ref:`restart Squid <system-administration-web-proxy-additional-configuration>`.

Squid associates successful NTLM authentication with the client TCP connection.
A new TCP connection requires a new authentication.

The UCR variable :envvar:`squid/ntlmauth/keepalive`
controls Squid's NTLM ``keep_alive`` setting.

By default, all users can access the proxy.
To limit proxy access to one or more groups,
enable a proxy authentication mechanism
and set the UCR variable :envvar:`squid/auth/allowed_groups`
to the LDAP group names.
The setting matches the groups' ``cn`` values.

If you specify multiple groups, separate them with semicolons.
Don't add spaces around the semicolons.
After you change the setting,
:ref:`restart Squid <system-administration-web-proxy-additional-configuration>`.

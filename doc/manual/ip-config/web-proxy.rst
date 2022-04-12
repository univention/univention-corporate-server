.. _ip-config-web-proxy-for-caching-and-policy-management-virus-scan:

Web proxy for caching and policy management / virus scan
========================================================

The UCS proxy integration allows the use of a web cache for improving the
performance and controlling data traffic. It is based on the tried-and-tested
proxy server Squid and supports the protocols HTTP, FTP and HTTPS.

A proxy server receives requests about Internet contents and verifies whether
these contents are already available in a local cache. If this is the case, the
requested data are provided from the local cache. If the data are not available,
these contents are called up from the respective web server and inserted in the
local cache. This can be used to reduce the answering times for the users and
the transfer volume via the Internet access.

Further documentation on proxy services - such as the cascading of proxy
servers, transparent proxies and the integration of a virus scan engine - are
documented in `Extended IP and network management documentation
<https://docs.software-univention.de/networks-5.0.html>`_.

.. _ip-config-installation:

Installation
------------

Squid can be installed from the Univention App Center with the application
:program:`Web proxy / web cache (Squid)`. Alternatively, the software package
:program:`univention-squid` can be installed. Additional information can be
found in :ref:`computers-softwaremanagement-installsoftware`.

The service is configured with standard settings sufficient for operation so
that it can be used immediately. It is possible to configure the port on which
the service is accessible to suit your preferences (see :ref:`proxy-port`); port
``3128`` is set as default.

If changes are made to the configuration, Squid must be restarted. This can be
performed either via the UMC module :guilabel:`System services` or the command
line:

.. code-block:: console

   $ systemctl restart squid

In addition to the configuration possibilities via |UCSUCR| described in this
document, it is also possible to set additional Squid configuration options in
the :file:`/etc/squid/local.conf`.

.. _ip-config-caching-of-web-content:

Caching of web content
----------------------

Squid is a caching proxy, i.e., previously viewed contents can be provided from
a cache without being reloaded from the respective web server. This reduces the
incoming traffic via the Internet connection and can result in quicker responses
of HTTP requests.

However, this caching function is not necessary for some environments or, in the
case of cascaded proxies, it should not be activated for all of them. For these
scenarios, the caching function of the Squid can be deactivated with the
|UCSUCRV| :envvar:`squid/cache` by setting this to ``no``. Squid must then be
restarted.

.. _ip-config-logging-proxy-accesses:

Logging proxy accesses
----------------------

All accesses performed via the proxy server are stored in the logfile
:file:`/var/log/squid/access.log`. It can be used to follow which websites have
been accessed by the users.

.. _ip-config-restriction-of-access-to-permitted-networks:

Restriction of access to permitted networks
-------------------------------------------

As standard, the proxy server can only be accessed from local networks. If, for
example, a network interface with the address ``192.0.2.10`` and the network
mask ``255.255.255.0`` is available on the computer on which Squid is installed,
only computers from the network ``192.0.2.0/24`` can access the proxy server.
Additional networks can be specified via the |UCSUCRV|
:envvar:`squid/allowfrom`. When doing so, the CIDR notation must be used;
several networks should be separated by blank spaces.

Example:

.. code-block:: console

   $ univention-config-registry set squid/allowfrom="192.0.2.0/24 192.0.3.0/24"

Once Squid has been restarted, access is now permitted from the networks
``192.0.2.0/24`` and ``192.0.3.0/24``. If configured to ``all``, proxy access in
granted from all networks.

.. _ip-config-configuration-of-the-ports-used:

Configuration of the ports used
-------------------------------

.. _proxy-port:

Access port
~~~~~~~~~~~

As standard, the web proxy can be accessed via port ``3128``. If another port is
required, this can be configured via the |UCSUCRV| :envvar:`squid/httpport`. If
Univention Firewall is used, the packet filter configuration must also be
adjusted.

.. _ip-config-permitted-ports:

Permitted ports
~~~~~~~~~~~~~~~

In the standard configuration, Squid only forwards client requests intended for
the network ports 80 (HTTP), 443 (HTTPS) or 21 (FTP). The list of permitted
ports can be changed via the |UCSUCRV| :envvar:`squid/webports`; several entries
should be separated by blank spaces.

Example:

.. code-block:: console

   $ univention-config-registry set squid/webports="80 443"


With this setting, access is only allowed to ports 80 and 443 (HTTP and HTTPS).

.. _proxy-userauth:

User authentication on the proxy
--------------------------------

It is sometimes necessary to restrict web access to certain users. Squid allows
user-specific access regulation via group memberships. To allow verification of
group membership, it is necessary for the user to authenticate on the proxy
server.

.. caution::

   To prevent unauthorized users from opening websites nonetheless, additional
   measures are required to prevent these users from bypassing the proxy server
   and accessing the Internet. This can be done, for example, by limiting all
   HTTP traffic through a firewall.

The proxy authentication (and as a result the possible verification of the group
memberships) must firstly be enabled. There are three possible mechanisms for
this:

LDAP server authentication
   Direct authentication against the LDAP server. This is done by setting the
   |UCSUCRV| :envvar:`squid/basicauth` to ``yes`` and restarting Squid.

NTML authentication
   Authentication is performed via the NTLM interface. Users logged in on a
   Windows client then do not need to authenticate themselves again when
   accessing the proxy. NTLM authentication is enabled by setting the |UCSUCRV|
   :envvar:`squid/ntlmauth` to ``yes`` and restarting Squid.

Kerberos authentication
   Authentication is performed via Kerberos. Users logged in on a Windows client
   which is a member of a Samba/AD domain authenticate themselves on the proxy
   with the ticket that they received when they logged in to the domain. The
   :program:`univention-squid-kerberos` package must be installed on every proxy
   server for it to be possible to enable Kerberos authentication. Then the
   |UCSUCRV| :envvar:`squid/krb5auth` must be set to ``yes`` and Squid
   restarted.

If NTLM is used an NTLM authentication is performed for every HTTP query as
standard. If for example the website ``https://www.univention.de/`` is opened,
the subpages and images are loaded in addition to the actual HTML page. The NTLM
authentication can be cached per domain: If the |UCSUCRV|
:envvar:`squid/ntlmauth/keepalive` is set to ``yes``, no further NTLM
authentication is performed for subsequent HTML queries in the same domain. In
case of problems with local user accounts it may help to set this variable to
``no``.

In the standard setting all users can access the proxy. The |UCSUCRV|
:envvar:`squid/auth/allowed_groups` can be used to limit the proxy access to one
or several groups. If several groups are specified, they must be separated by a
semicolon.

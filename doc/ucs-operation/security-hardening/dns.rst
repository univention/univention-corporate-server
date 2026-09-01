.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-dns:

Restrict DNS exposure
=====================

DNS contains information about hosts, services, and the structure of a
domain.
Restrict zone transfers and queries to the systems that require them.

.. _security-hardening-dns-transfers:

Restrict zone transfers
-----------------------

The :envvar:`dns/allow/transfer` UCR variable controls which systems can
request DNS zone transfers when the LDAP backend is in use.
Don't use ``any`` on a production DNS server.
Use ``none`` when zone transfers aren't required:

.. code-block:: console

   $ ucr set dns/allow/transfer=none

If secondary DNS servers require transfers, specify their IP addresses or
networks, separated by semicolons:

.. code-block:: console

   $ ucr set 'dns/allow/transfer=192.0.2.53;192.0.2.54'

An ACL in ``/etc/bind/local.conf`` can also be referenced by this variable.
Update the allow list when adding or removing secondary servers.

.. _security-hardening-dns-queries:

Restrict DNS queries
--------------------

Review :envvar:`dns/allow/query` when the DNS service isn't intended to serve
the entire network.
Use an allow list of required networks instead of ``any`` where the network
design permits it.
Don't block queries from UCS systems that need DNS for domain discovery,
Kerberos, or replication.

An administrator with root access to a Samba/AD domain controller can modify
DNS data.
Treat such systems as domain-critical and protect their administrative access
accordingly.

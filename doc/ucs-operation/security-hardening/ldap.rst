.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-ldap:

Harden LDAP transport
=====================

OpenLDAP uses TLS to protect directory connections.
Encryption protects credentials and directory data in transit, but it doesn't
replace certificate validation or access controls.

For LDAP architecture and connection endpoints, see
:ref:`domain-infrastructure-ldap-directory`.

.. _security-hardening-ldap-tls:

Require a modern TLS version
----------------------------

The UCR variable :envvar:`ldap/tls/minprotocol` uses OpenSSL protocol values:

* ``3.1`` represents TLS 1.0.
* ``3.2`` represents TLS 1.1.
* ``3.3`` represents TLS 1.2.

Use at least TLS 1.2 where all LDAP clients support it:

.. code-block:: console

   $ ucr set ldap/tls/minprotocol=3.3

Changing this setting can break older applications, domain integrations, and
monitoring clients.
Test authenticated binds, replication, and all applications that use LDAP.

.. _security-hardening-ldap-ciphers:

Review LDAP cipher suites
-------------------------

The :envvar:`ldap/tls/ciphersuite` UCR variable controls the cryptographic
algorithms offered during a TLS handshake.
Keep the UCS default unless you have a tested organization-wide TLS policy.
If you define a custom value, exclude anonymous authentication, obsolete
hashes, and algorithms that the policy prohibits:

.. code-block:: console

   $ ucr set ldap/tls/ciphersuite='HIGH:MEDIUM:!aNULL:!MD5:!RC4'

The syntax is interpreted by OpenSSL and depends on the installed OpenSSL
version.
Validate the resulting configuration with the LDAP clients that the system
must support.

.. _security-hardening-ldap-access:

Disable anonymous LDAP reads
----------------------------

The UCR variable :envvar:`ldap/acl/read/anonymous` controls unauthenticated
LDAP reads.
Keep it disabled:

.. code-block:: console

   $ ucr set ldap/acl/read/anonymous=no

Review :envvar:`ldap/acl/read/ips` as well.
Entries there grant anonymous read access to selected IP addresses even when
general anonymous reads are disabled.
Remove entries that aren't required by a local service.

Don't permit simple binds over unencrypted LDAP connections.
Require TLS or another protected transport for clients that send credentials,
and check connector settings so that Active Directory and LDAP connections
don't disable certificate or transport verification.

.. _security-hardening-ldap-dh:

Maintain Diffie-Hellman parameters
----------------------------------

OpenLDAP can periodically recreate Diffie-Hellman parameters for ephemeral key
exchange.
Configure a suitable interval through :envvar:`ldap/tls/dh/cron` and verify
that the configured parameter file in :envvar:`ldap/tls/dh/paramfile` has
appropriate permissions.
If the LDAP service must restart after regeneration, configure
:envvar:`ldap/tls/dh/restart` and schedule the restart for a maintenance
window.

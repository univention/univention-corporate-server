.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-samba:

Harden Samba services
=====================

Samba provides file services and, in some environments, Active Directory
compatible domain controller services.
The correct hardening level depends on the clients, domain trusts, and
applications that connect to the service.

.. _security-hardening-samba-protocols:

Disable legacy SMB and NetBIOS
------------------------------

SMB1 has known security weaknesses.
Raise the minimum protocol level for incoming and outgoing connections:

.. code-block:: console

   $ ucr set samba/min/protocol=SMB2
   $ ucr set samba/client/min/protocol=SMB2

Use ``SMB3`` where all clients support it.
Test printers, embedded devices, and older file servers before applying the
change.

If the environment uses DNS and fully qualified hostnames instead of legacy
network browsing, disable the NetBIOS service:

.. code-block:: console

   $ ucr set samba4/service/nmb=''

Older Windows clients can depend on NetBIOS browsing or short names.
Keep the service enabled until those dependencies have been migrated.

.. _security-hardening-samba-authentication:

Restrict authentication and signing
------------------------------------

Keep NTLM restricted to NTLMv2 where compatibility permits it:

.. code-block:: console

   $ ucr set samba/ntlm/auth=ntlmv2-only
   $ ucr set samba/server/signing=mandatory

Mandatory signing provides integrity protection against some tampering and
man-in-the-middle attacks.
It can prevent connections from clients that don't support signing and can
affect performance.

To limit anonymous account and share enumeration, configure the Samba global
option:

.. code-block:: console

   $ ucr set 'samba/global/options/restrict anonymous=2'

Restart Samba after changing Samba configuration and test file access from
the clients that you support.

On UCS systems installed before UCS 5.0, inspect the effective
``acl:search`` setting:

.. code-block:: console

   $ samba-tool testparm --suppress-prompt | grep 'acl:search'

Set :envvar:`samba/acl_search` to ``yes`` if the effective value is ``no``.
Apply the setting on every Samba/AD domain controller and then restart Samba.
This setting controls whether Samba searches access control lists when
processing requests.

Reduce vendor and hostname disclosure in SMB discovery responses by setting a
generic server string:

.. code-block:: console

   $ ucr set samba/serverstring='File Server'

The default value can disclose the hostname and the UCS product name through
``net view`` and the print manager.

.. _security-hardening-samba-tls:

Configure Samba TLS
-------------------

Samba uses GnuTLS for TLS connections in the Samba/AD domain controller.
The :envvar:`samba/tls/priority` variable accepts a GnuTLS priority string.
The UCS default excludes SSL 3.0.
You can use a stricter policy that permits TLS 1.2 with AES-GCM, but test it
with all domain clients and integrations first:

.. code-block:: console

   $ ucr set samba/tls/priority='NORMAL:-VERS-SSL3.0:-VERS-TLS1.0:-VERS-TLS1.1:-CIPHER-ALL:-SHA1:-MD5:-RSA:-ARCFOUR-128:+AES-256-GCM:+AES-128-GCM:%SERVER_PRECEDENCE'

The priority string isn't a universal compatibility setting.
In particular, older Windows clients can no longer connect after this change.
Use :program:`gnutls-cli` to inspect available ciphers and test a service
endpoint before rolling out the setting.

For example, install the GnuTLS tools and test the local AD DC endpoint with
the selected priority string:

.. code-block:: console

   $ univention-install gnutls-bin
   $ gnutls-cli -l
   $ gnutls-cli --priority 'NORMAL:-VERS-SSL3.0' -p 636 $(hostname -f)

To use Diffie-Hellman key exchange, create a parameter file and configure it
on every relevant Samba/AD domain controller:

.. code-block:: console

   $ openssl dhparam -out /etc/univention/ssl/samba_dhparams.pem 2048
   $ ucr set samba/tls/dh/params/file=/etc/univention/ssl/samba_dhparams.pem

Protect the parameter file and plan the service restart required to activate
the configuration.

.. _security-hardening-samba-ad:

Review Active Directory-specific settings
------------------------------------------

Not every Active Directory hardening recommendation applies to Samba.
In particular, don't change domain groups, machine-account behavior, or
replication settings without checking the Samba implementation and the UCS
integration.

Use a Read-Only Domain Controller (RODC) and tiered administration where the
domain design requires reduced exposure of credentials on a site or server.
Review the Active Directory Connection, trusts, service accounts, and LAPS
deployment as part of that design.

On Samba/AD domain controllers, setting
:envvar:`samba/kdc_default_domain_supported_enctypes` to
``aes256-cts-hmac-sha1-96,aes128-cts-hmac-sha1-96`` disables RC4-HMAC as a
default supported encryption type for accounts where
``msDS-SupportedEncryptionTypes`` is unset or set to ``0``.

Disabling RC4-HMAC mitigates Kerberoasting and AS-REP-Roasting attacks by
preventing the use of the comparatively weak RC4-based password-derived key
for such tickets. It does not prevent these attacks in general, as tickets
using AES encryption types can also be subject to offline password guessing.

Before disabling RC4-HMAC, verify that no service accounts or clients still
depend on RC4-only Kerberos authentication: Coordinate this setting with
:ref:`security-hardening-kerberos`.


An administrator with root access on a Samba/AD DC can change DNS data and
other domain-critical settings.
A Samba/AD DC on a secondary site participates in multi-primary replication;
it isn't a security boundary by itself.
Use an RODC and tiered administration when the site requires reduced
credential exposure.

The Active Directory Connection can also use LDAP connections to the remote
directory.
Don't disable TLS or certificate verification for that connection to work
around a certificate problem.
An unprotected connection permits interception or manipulation of directory
traffic.

When Samba domain password history is enabled, Samba can accept the previous
password for NTLM network authentication for a grace period.
The default period is 60 minutes.
If your compatibility requirements permit it, set the Samba
``old password allowed period`` parameter to ``0`` in the local Samba
configuration on every Samba/AD domain controller.
This is a local Samba setting and isn't controlled by a UCR variable.

For curated Active Directory guidance, see the
`Microsoft Active Directory security best practices
<https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory>`_,
the `Microsoft privileged access model
<https://learn.microsoft.com/en-us/security/privileged-access-workstations/privileged-access-access-model>`_,
and the `SpecterOps Tier Zero reference
<https://specterops.github.io/TierZeroTable/>`_.
Apply guidance to Samba only after checking the corresponding Samba behavior.

The :ref:`security-hardening-kerberos` chapter covers the credential material
and Kerberos encryption types that also affect Samba/AD environments.

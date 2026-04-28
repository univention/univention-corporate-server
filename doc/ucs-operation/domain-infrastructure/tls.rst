.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-tls:

Certificate management
======================

Nubus for UCS always encrypts sensitive data in transit.
For example, it uses SSH for signing in to systems
and TLS for domain replication and LDAP communication.

Each computer must verify each other's identity before exchanging encrypted data.
To do this,
each computer has a *host certificate*
that a certification authority (CA) issues and signs.

This section describes the built-in UCS certificate authority,
which manages trust within the Nubus for UCS domain.
For publicly trusted certificates for web-facing services such as Apache,
see :ref:`lifecycle-lets-encrypt`.

.. _domain-infrastructure-tls-ca:

UCS built-in certificate authority
----------------------------------

Nubus for UCS automatically creates its own CA when you install the :term:`Primary Directory Node`.
When a Nubus for UCS system joins the domain,
it automatically requests its own host certificate
and retrieves the CA's public certificate.
The CA acts as the root CA:
it signs its own certificate,
and can sign certificates for subordinate CAs.

The UCS CA secures communication within the Nubus for UCS domain,
not public-facing web services.

Nubus for UCS generates the CA properties automatically during installation,
based on system settings such as the locale.
To change these settings after installation,
open the *Certificate settings* module in the *Management UI*
on the Primary Directory Node.

.. caution::

   If you change the root certificate through the *Certificate settings* module,
   you must reissue all host certificates.
   See :uv:kb:`Renewing the SSL/TLS certificates <37>`.

The CA in Nubus for UCS resides on the Primary Directory Node.
Every :term:`Backup Directory Node` stores a copy of the CA.
A cron job updates each copy from the Primary Directory Node every 20 minutes.

.. important::

   CA updates transfer only from the Primary Directory Node to the Backup Directory Node,
   not in the other direction.
   Always use the CA on the Primary Directory Node.

If you promote a Backup Directory Node to the Primary Directory Node,
you can immediately use the CA on the new Primary Directory Node.
For more information about the promotion,
see :ref:`deployment-primary-dn-resilience-backup-primary-promotion`.

.. seealso::

   :ref:`deployment-domain-setup-new-domain`
      for information about the installation of a Primary Directory Node

   :ref:`deployment-domain-setup-join-ucs`
      for information about a Nubus for UCS joining a domain.

.. _domain-infrastructure-tls-validity:

Certificate validity
--------------------

The Nubus for UCS root certificate and all host certificates issued from it expire after a set period.
To renew the root certificate and all host certificates,
see :uv:kb:`Renewing the SSL/TLS certificates <37>`.

.. caution::

   When a certificate expires,
   services that use TLS-encrypted communication,
   such as LDAP or domain replication,
   stop working.

.. _domain-infrastructure-tls-monitoring:

Monitor certificate expiry
--------------------------

Nubus for UCS monitors certificate validity automatically.
The Nagios plugin monitors the validity period,
and the *Management UI* shows a warning
when the root certificate is about to expire.
You can configure the warning period with the :term:`UCR variable`
:envvar:`ssl/validity/warning`.
The default warning period is 30 days.
You must renew the root certificate before the root certificate expires.

Each day, a separate cron job on Nubus for UCS systems checks the validity of the host certificate
and the root certificate.
The cron job stores the expiry dates in the following UCR variables.
These values are the number of days since 1970-01-01.

:Host certificate: :envvar:`ssl/validity/host`
:Root certificate: :envvar:`ssl/validity/root`

To download the root certificate and the certificate revocation list in the *Management UI*:

#. Open the hamburger menu.
#. For the root certificate select :menuselection:`Certificates --> Root certificate`.
#. For the revocation list select :menuselection:`Certificates --> Certificate revocation list`.

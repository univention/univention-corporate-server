.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _lifecycle-lets-encrypt:

Let's Encrypt
=============

Let's Encrypt is a non-profit certificate authority
that provides X.509 certificates for TLS encryption at no charge.
Use it to secure public-facing services in Nubus for UCS
with certificates that browsers and operating systems trust.
The *Let's Encrypt* app in Univention App Center provides automated
integration of the :program:`acme-tiny` client in Nubus for UCS.
The app secures the Apache web server, the Postfix SMTP mail server,
and the Dovecot IMAP mail server.

.. seealso::

   :ref:`domain-infrastructure-tls`
      For information about the built-in UCS certificate authority for domain-internal services.

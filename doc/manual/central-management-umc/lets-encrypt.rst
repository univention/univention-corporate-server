.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _central-management-umc-lets-encrypt:

Let's Encrypt
=============

Let's Encrypt is a non-profit certificate authority that provides X.509
certificates for TLS encryption at no charge. It is the world's largest
certificate authority with the goal of all websites being secure and using
HTTPS.

The :program:`Let's Encrypt` app in Univention App Center offers a largely automated
integration of the *acme-tiny Let's Encrypt client* in UCS. The supported services
in UCS are the Apache Web server, the Postfix SMTP mail server and the Dovecot
IMAP mail server.

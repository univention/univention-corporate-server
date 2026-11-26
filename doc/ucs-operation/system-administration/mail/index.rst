.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-mail:

Mail services
=============

Nubus for UCS provides mail services
that users can access through standard email clients.
The mail services use :program:`Postfix` to send and receive email
and :program:`Dovecot` to provide access to mailboxes through IMAP and POP3.

In the basic Nubus for UCS installation, Postfix accepts email only from the local system
and delivers it only to local system users.
To provide mail services for domain users,
install the mail server as described in :ref:`system-administration-mail-install`.
The mail server uses the LDAP directory
to check incoming email addresses and manage mailbox information.

You can manage mail domains, user email addresses, mailing lists,
mail groups, and shared IMAP folders through the *Management UI*.
For information about managing these mail objects,
see :external+uv-nubus-manual:ref:`nubus-domain-mail`.

.. toctree::

   install

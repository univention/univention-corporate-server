.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-mail-install:

Install the mail server
=======================

You can install the mail server on a Nubus for UCS system with any system role.
Univention recommends a Directory Node
because the mail server frequently accesses the LDAP directory.

Install the :program:`Mail server` app through Univention App Center.
For instructions, see :ref:`lifecycle-app-center-installation`.

Alternatively, you can install the :program:`univention-mail-server` package.
For information about package installation,
see :ref:`lifecycle-package-installation-management`.

Dovecot stores its runtime data in :file:`/var/spool/dovecot/`.
If you use an NFS share for this directory,
see :external+uv-ucs-manual:ref:`mail-serverconfig-nfs`.

.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _mail-installation:

Installation
============

A mail server can be installed from the Univention App Center with the
application :program:`Mail server`. Alternatively, the software package
:program:`univention-mail-server` can be installed. Additional information can
be found in :ref:`computers-softwaremanagement-install-software`. A mail server
can be installed on all server system roles. The use of a UCS Directory Node is
recommended because of frequent LDAP accesses.

The runtime data of the Dovecot server are stored in the
:file:`/var/spool/dovecot/` directory. If this directory is on a NFS share,
please read :ref:`mail-serverconfig-nfs`.

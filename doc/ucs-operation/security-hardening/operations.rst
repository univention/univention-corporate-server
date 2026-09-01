.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _security-hardening-operations:

Harden system operations
========================

Security controls are effective only when you can detect changes, restore
systems, and investigate incidents.
Combine the service settings in this chapter with regular updates, tested
backups, access control, and monitoring.

.. _security-hardening-operations-updates:

Protect update integrity
------------------------

Keep updater script signature verification enabled:

.. code-block:: console

   $ ucr set repository/online/verify=yes

The :envvar:`repository/online/verify` UCR variable controls verification of
downloaded updater scripts.
Disabling it removes an important integrity check and can allow tampered
scripts to run with system privileges.

Install security updates through the supported update process.
Don't disable signature verification to work around a repository or package
problem.

.. _security-hardening-operations-monitoring:

Monitor privileged changes
--------------------------

Enable directory change logging with the directory logger when your audit
requirements include changes to the LDAP directory.
Use a command-audit component, such as the Linux Audit system, when you need
to record privileged commands run on the shell.
Forward relevant events to central monitoring with alerting and reporting.

Protect monitoring data from unauthorized changes and test that alerts arrive
at the responsible administrators.

Use the LDAP directory logging facilities to record directory changes.
For more information about LDAP data and administration, see
:ref:`domain-infrastructure-ldap-directory`.

Review listener share allow lists as part of the service inventory.
Keep only the paths that installed services require in the
``listener/shares/whitelist/*`` UCR variables.
An unnecessarily broad allow list increases the number of files that a
listener can process after a change event.

For repeatable configuration across multiple systems, you can use the
`Univention hardening Ansible role
<https://github.com/univention/ansible-roles/tree/main/roles/hardening>`_.
Review the role version and its changes before applying it to production.

.. _security-hardening-operations-time:

Synchronize system time
-----------------------

Accurate, synchronized clocks are required for Kerberos authentication and
are important for correlating audit events.
Configure at least one external time server for the Primary Directory Node
through :envvar:`timeserver`.
Other UCS systems use the Primary Directory Node as their upstream time
server by default.

For the complete time configuration procedure, see
:ref:`system-administration-regional-settings`.

.. _security-hardening-operations-databases:

Limit database exposure
-----------------------

Install only the database services that your applications require.
Remove anonymous database accounts, disable remote root access, and remove
test databases when using MySQL or MariaDB.
Store database credentials with the service that requires them and restrict
their permissions.

For :program:`univention-mysql`, bind the service only to the interfaces that
need it through :envvar:`mysql/config/mysqld/bind_address`.
Review packet filter rules before exposing MySQL or PostgreSQL to another
system.
Permit access only from the required application hosts and ports.

.. _security-hardening-operations-backups:

Protect and test backups
------------------------

Create regular backups and limit access to them.
Encrypt backup media when it contains directory data, credentials, or other
sensitive information.
Perform restore tests so that a backup is a usable recovery method rather
than only an archive.

.. _security-hardening-operations-passwords:

Review local password hashes
----------------------------

The :ref:`password-management-hashes` page describes LDAP password hashes.
Local accounts use a separate password database.
After upgrading an older UCS installation, change the local ``root``
password if it was created before the system switched from the obsolete
``md5crypt`` format to ``sha512crypt``.
This causes the local account to receive a current hash format.

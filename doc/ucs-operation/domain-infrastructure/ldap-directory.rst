.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-ldap-directory:

LDAP directory service
======================

.. highlight:: console

Nubus for UCS stores domain-wide data
in an LDAP directory service that uses OpenLDAP.
This chapter covers advanced OpenLDAP configuration
and LDAP coordination.
A Nubus for UCS domain often uses several LDAP servers.
For information about configuring the LDAP servers in use,
see :ref:`system-administration-ldap-server`.

.. _domain-infrastructure-ldap-directory-schema-and-replication:

Schema and replication
----------------------

This section describes LDAP schemas,
LDAP extensions, and schema replication
in a Nubus for UCS domain.

.. _domain-infrastructure-ldap-directory-schema:

LDAP schemas
~~~~~~~~~~~~

Schema definitions specify the object classes and attributes
that a directory service can store and manage.
OpenLDAP stores schema definitions in text files
and includes them in its configuration file.

Nubus for UCS uses standard schemas where possible
to support interoperability with other LDAP applications.
It also provides Univention-specific schema extensions
for attributes such as the policy mechanism.

.. _domain-infrastructure-ldap-directory-schema-extension:

LDAP schema extensions
~~~~~~~~~~~~~~~~~~~~~~

For custom LDAP extensions,
Nubus for UCS provides its own LDAP schema.
The LDAP object class ``univentionFreeAttributes`` provides
20 attributes, from ``univentionFreeAttribute1``
to ``univentionFreeAttribute20``,
for unrestricted extension attributes.
You can use this object class with any LDAP object,
for example, a user object.

If you deliver LDAP schema extensions as part of a software package,
you can package them
and distribute them to all :term:`Backup Directory Node` systems
in the domain through a Univention Directory Listener module.
For more information,
see :ref:`uv-dev-ref:settings-ldapschema`
in :cite:t:`developer-reference`.

.. _domain-infrastructure-ldap-directory-schema-replication:

LDAP schema replication
~~~~~~~~~~~~~~~~~~~~~~~

The listener and notifier mechanism automates LDAP schema replication.
For more information,
see :ref:`listener-notifier`.
Because schema replication runs before LDAP object replication,
object replication doesn't fail because of missing object classes
or attributes.
This automation means that you don't need to update
every OpenLDAP server in the domain manually.

When the OpenLDAP server starts on the :term:`Primary Directory Node`,
it calculates a checksum for all directories
that contain schema definitions.
The server compares this checksum with the previously saved checksum in
:file:`/var/lib/univention-ldap/schema/md5`.

The Univention Directory Listener starts schema replication.
Before it requests a new transaction ID
from the Univention Directory Notifier,
it requests the current schema ID.
If that schema ID is higher than the schema ID
on the listener system,
the listener retrieves the current sub-schema
from the notifier system's LDAP server
through an LDAP search.

The listener writes the resulting sub-schema in LDIF format
to :file:`/var/lib/univention-ldap/schema.conf`.
Then it restarts the local OpenLDAP server.
After the listener completes schema replication,
LDAP object replication continues.

.. seealso::

   :ref:`listener-notifier`
      for information about the listener and notifier mechanism.

.. _domain-infrastructure-ldap-directory-operations-and-maintenance:

Operations and maintenance
--------------------------

This section describes logging, connection timeout settings,
and LDAP backup tasks.

.. _domain-infrastructure-ldap-directory-logger:

Tamper-evident logging of LDAP changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :program:`univention-directory-logger` package logs all changes
to the LDAP directory.
Because each data record includes a hash of the previous record,
you can detect changes to the log file,
such as deleted entries.

To install the :program:`univention-directory-logger` package,
follow the instructions in
:ref:`lifecycle-package-installation-management-umc`
or
:ref:`lifecycle-package-installation-management-commandline`.

You can exclude specific directory branches from logging.
Configure these branches with numbered :term:`UCR variables <UCR variable>`
such as :envvar:`ldap/logging/exclude1`,
:envvar:`ldap/logging/exclude2`,
and :envvar:`ldap/logging/exclude3`.
Set each variable to a DN fragment,
for example ``cn=temporary,cn=univention,$ldap_base``.
By default, the logger excludes the temporary object container,
``cn=temporary,cn=univention``.

After you change these UCR variables,
restart the Univention Directory Listener service,
as shown in :numref:`domain-infrastructure-ldap-directory-logger-restart-listing`.
Then verify the result in
:file:`/var/log/univention/directory-logger.log`
by changing an object in an excluded branch
and confirming that the log file doesn't contain a new entry for that change.

.. code-block::
   :caption: Restart Univention Directory Listener service
   :name: domain-infrastructure-ldap-directory-logger-restart-listing

   $ systemctl restart univention-directory-listener.service

The :program:`univention-directory-logger` package writes log entries to
:file:`/var/log/univention/directory-logger.log`.
:numref:`lst-ldap-directory-logger-format` shows the log entry format.

.. code-block:: none
   :caption: Log entry format in ``directory-logger.log``
   :name: lst-ldap-directory-logger-format

   START
   Old Hash: […]
   DN:[…]
   ID: […]
   Modifier: […]
   Timestamp: […]
   Action: […]

   Old Values:
    […]
   New Values:
    […]
   END

The fields in :numref:`lst-ldap-directory-logger-format`
have the following meanings:

:``Old Hash``: Identifies the hash sum of the previous data record.
:``DN``: Identifies the distinguished name (DN) of the LDAP object.
:``ID``: Identifies the listener/notifier transaction ID.
:``Modifier``: Identifies the distinguished name (DN) of the modifying account.
:``Timestamp``: Shows the timestamp in the format ``dd.mm.yyyy hh:mm:ss``.
:``Action``: Identifies whether the action adds, modifies, or deletes the object.
:``Old Values``: Lists the previous attribute values.
   This field is empty after Nubus adds an object.
:``New Values``: Lists the new attribute values.
   This field is empty after Nubus deletes an object.

Nubus calculates a hash sum for each logged data record
and writes it to the ``daemon.info`` facility of the syslog service.

:uv:erratum:`4.4x536` adds the transaction ID of the entry
as a prefix before each line in
:file:`/var/log/univention/directory-logger.log`,
as shown in :numref:`lst-ldap-directory-logger-id-prefix`.
On systems with an earlier :program:`univention-directory-logger` package version,
the package keeps the old behavior without the prefix by default.
Set the :term:`UCR variable` :envvar:`ldap/logging/id-prefix` value to ``yes``
to enable the prefix.
This transaction ID lets you correlate related lines
for log analysis and monitoring.

.. code-block:: none
   :caption: Log entry format with transaction ID prefix
   :name: lst-ldap-directory-logger-id-prefix

   ID 342: START
   ID 342: Old Hash: 70069d51a7e2e168d7c7defd19349985
   ID 342: DN: uid=Administrator,cn=users,dc=example,dc=com
   ID 342: ID: 342
   ID 342: Modifier: cn=admin,dc=example,dc=com
   ID 342: Timestamp: 15.04.2020 09:20:40
   ID 342: Action: modify
   ID 342:
   ID 342: Old values:
   ID 342: description: This is a description test
   ID 342: entryCSN: 20200415091936.317108Z#000000#000#000000
   ID 342: modifyTimestamp: 20200415091936Z
   ID 342:
   ID 342: New values:
   ID 342: description: This is a description test
   ID 342: entryCSN: 20200415092040.430976Z#000000#000#000000
   ID 342: modifyTimestamp: 20200415092040Z
   ID 342: END

.. _domain-infrastructure-ldap-directory-timeout-inactive-connections:

Timeout for inactive LDAP connections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :term:`UCR variable` :envvar:`ldap/idletimeout`
defines the timeout duration, in seconds, for inactive LDAP connections.
If you set the value to ``0``,
the server doesn't enforce a timeout.
By default, the timeout is six minutes.

.. _domain-infrastructure-ldap-directory-backup:

Daily backup of LDAP data
~~~~~~~~~~~~~~~~~~~~~~~~~

A cron job backs up LDAP directory data every day
on the :term:`Primary Directory Node`
and all :term:`Backup Directory Node` systems.
If you use Samba,
the cron job also backs up its data directory.

The system stores LDAP data in LDIF format in
:file:`/var/univention-backup/`
with filenames that follow the pattern
:file:`ldap-backup_{DATE}.ldif.gz`.
Only the ``root`` user can read these files.
The system stores Samba files in
:file:`/var/univention-backup/samba/`.

Use the :term:`UCR variable` :envvar:`backup/clean/max_age`
to define how long the system keeps old backup files.
If you set :envvar:`backup/clean/max_age` to ``365``,
the system deletes backup files
that are older than 365 days.
If you don't set the variable,
the system doesn't delete old backup files automatically.
After the backup runs,
verify that a new timestamped backup file exists in
:file:`/var/univention-backup/`.
If you use Samba,
also verify that a new backup file exists in
:file:`/var/univention-backup/samba/`.

.. _domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap:

Restart the LDAP server
~~~~~~~~~~~~~~~~~~~~~~~

To restart the LDAP server use the command in
:numref:`domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap-listing`.
The LDAP server is temporarily unavailable during the restart.

.. code-block:: console
   :caption: Restart the OpenLDAP server
   :name: domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap-listing

   $ systemctl restart slapd.service

.. _domain-infrastructure-ldap-directory-access-control:

Access control
--------------

This section describes LDAP access control settings,
anonymous access,
nested groups,
and delegated password resets.

.. _domain-infrastructure-ldap-directory-acls:

LDAP access control configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Server-side Access Control Lists (ACLs)
control access to information in the LDAP directory.
The central configuration file :file:`/etc/ldap/slapd.conf`
defines these ACLs.
Univention Configuration Registry manages this configuration.

A multifile template manages :file:`slapd.conf`.
To add ACL elements,
create or extend a template in
:file:`/etc/univention/templates/files/etc/ldap/slapd.conf.d/`
between
:file:`60univention-ldap-server_acl-master`
and
:file:`70univention-ldap-server_acl-master-end`.
You can also extend the existing UCR templates.
For information about how to modify existing UCR templates,
see :ref:`system-administration-ucr-templates`.

After you change the template,
run ``ucr commit /etc/ldap/slapd.conf``.
Then :ref:`domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap`.
Verify the ACL change with one test account
with access
and one test account without access.

If you deliver LDAP ACL extensions as part of software packages,
you can package them
and distribute them to all LDAP servers in the domain
through a Univention Directory Listener module.
For more information,
see :ref:`uv-dev-ref:settings-ldapacl`
in :cite:t:`developer-reference`.

.. _domain-infrastructure-ldap-directory-acls-anonymous:

Anonymous read access
~~~~~~~~~~~~~~~~~~~~~

By default, a new installation of Nubus for UCS
doesn't allow anonymous access to the LDAP directory.
Use the :term:`UCR variable` :envvar:`ldap/acl/read/anonymous`
to control whether the LDAP server allows anonymous read access.
Use the :term:`UCR variable` :envvar:`ldap/acl/read/ips`
to allow anonymous read access only from specific IP addresses.

After you change these UCR variables,
:ref:`domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap`.
Then test anonymous access from an allowed client
and from a disallowed client.

After a user authenticates on the LDAP server,
that user can read all attributes of their own user account.

The internal root DN account also has full write access.

Nubus for UCS also includes additional ACLs by default.
These ACLs block access to sensitive attributes,
for example, user passwords,
and define the access rules that the system needs for operation,
for example, access to computer accounts during sign-in.
Only members of the ``Domain Admins`` group
can read or write this sensitive information.

.. _domain-infrastructure-ldap-directory-acls-nested-groups:

Nested group handling
~~~~~~~~~~~~~~~~~~~~~

Nubus for UCS supports nested groups.
Use the :term:`UCR variable` :envvar:`ldap/acl/nestedgroups`
to deactivate nested groups for LDAP ACLs.
Deactivating nested groups can speed up directory requests,
but LDAP ACLs then no longer evaluate nested group membership.

After you change this UCR variable,
:ref:`domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap`.
Then test access with an account
that receives permissions through a nested group.

.. seealso::

   :ref:`ucs-operation-groups-management-nested`
      for more information about nested groups.

.. _domain-infrastructure-ldap-directory-delegate-password-reset:

Delegation of the privilege to reset user passwords
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delegate password resets,
install the :program:`univention-admingrp-user-passwordreset` package.
For package installation instructions,
see
:ref:`lifecycle-package-installation-management-umc`
or
:ref:`lifecycle-package-installation-management-commandline`.
Install the package on the :term:`Primary Directory Node`
and the :term:`Backup Directory Nodes <Backup Directory Node>`.
During installation,
the LDAP server restarts
and is temporarily unavailable.
The package runs a join script
that creates the ``User Password Admins`` group
if the group doesn't already exist.

Additional LDAP ACLs give members of this group permission
to reset other users' passwords.
The package activates these ACLs during installation.
If you want to use another group instead of ``User Password Admins``,
set the distinguished name (DN) of that group in the :term:`UCR variable`
:envvar:`ldap/acl/user/passwordreset/accesslist/groups/dn`.

By default,
only the ``Administrator`` user can access the
:external+uv-nubus-manual:ref:`nubus-user-management-users` management module.
During installation,
the package creates the ``default-user-password-admins`` policy
and links it to members of the ``User Password Admins`` group.

To allow delegated password resets:

#. Add each delegated administrator
   to the configured delegation group.

#. Assign the ``default-user-password-admins`` policy,
   or an equivalent policy,
   to the LDAP container where you want to allow password resets.

After you complete the configuration,
members of the delegation group can reset passwords
for users in the assigned container.
This policy also lets group members search for users
and view all attributes of a user object.
If a user without sufficient LDAP access rights
tries to modify attributes other than the password,
Univention Directory Manager denies the change
and shows the message *Permission denied*.

For more information about group membership,
see :external+uv-nubus-manual:ref:`nubus-user-management-users-tab-groups`.
For more information about policy assignment
and delegated administration,
see :external+uv-nubus-manual:ref:`nubus-domain-policies-assign`
and :ref:`management-interface-delegated-administration`.

You can prevent password resets through this group
for sensitive users or groups,
for example, domain administrators.
Use the :term:`UCR variables <UCR variable>`
:envvar:`ldap/acl/user/passwordreset/protected/uid`
and :envvar:`ldap/acl/user/passwordreset/protected/gid`
to define protected users and groups.
Separate multiple values with commas.

After you change these UCR variables,
:ref:`domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap`.
Then verify that delegated administrators can't reset passwords
for a protected user
or for a member of a protected group.
By default,
this delegation doesn't allow group members
to change passwords for members of the ``Domain Admins`` group.

If you need access to additional LDAP attributes
when you change a password,
add the attribute names to the :term:`UCR variable`
:envvar:`ldap/acl/user/passwordreset/attributes`.
Use a comma-separated list of LDAP attribute names.
A standard Nubus for UCS installation already sets this variable
for the default password reset workflow.
Add attributes only if your workflow requires additional LDAP attributes
during password changes.

After you change this UCR variable,
:ref:`domain-infrastructure-ldap-directory-operations-and-maintenance-restart-ldap`.
Then verify that the password reset workflow still works
for delegated administrators.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-user-management-users`
      in :cite:t:`uv-nubus-manual`
      for information about the :guilabel:`Users` management module.

   :external+uv-nubus-manual:ref:`nubus-user-management-users-tab-groups`.
      in :cite:t:`uv-nubus-manual`
      for reference information about the groups tab in the :guilabel:`Users` management module.

   :external+uv-nubus-manual:ref:`nubus-domain-policies-assign`
      in :cite:t:`uv-nubus-manual`
      for information about policy assignment.

.. _domain-infrastructure-ldap-directory-client-access-and-interoperability:

Client access and interoperability
----------------------------------

This section describes LDAP command-line tools,
Name Service Switch integration,
and directory service behavior with Samba in Nubus for UCS.

.. _domain-infrastructure-ldap-directory-cli-tools:

LDAP command line tools
~~~~~~~~~~~~~~~~~~~~~~~

In addition to LDAP access in the *Management UI*,
you can access the LDAP directory from the command line
with several programs.

The :command:`univention-ldapsearch` tool
simplifies authenticated searches in the LDAP directory.
Specify a search filter as an argument.
The example in :numref:`domain-infrastructure-ldap-directory-cli-tools-ldapsearch`
searches for the ``Administrator`` user by user ID.

.. code-block:: console
   :caption: Search for the ``Administrator`` user
   :name: domain-infrastructure-ldap-directory-cli-tools-ldapsearch

   $ univention-ldapsearch uid=Administrator

The :command:`slapcat` command saves the current LDAP data
to a text file in LDIF format.
The example in :numref:`domain-infrastructure-ldap-directory-cli-tools-slapcat`
writes the data to :file:`ldapdata.txt`.

.. code-block:: console
   :caption: Export LDAP data in LDIF format
   :name: domain-infrastructure-ldap-directory-cli-tools-slapcat

   $ slapcat -f /etc/ldap/slapd.conf > ldapdata.txt

.. _domain-infrastructure-ldap-directory-nss:

Name Service Switch and LDAP NSS module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *Name Service Switch* in the GNU C standard library
provides a modular interface
to resolve the names of users,
groups,
and hosts.

By default, Nubus for UCS uses the LDAP NSS module
to access domain data,
for example, user information.
The module queries the LDAP server specified in
the :term:`UCR variable` :envvar:`ldap/server/name`.
If that server is unavailable,
the module can query the server specified in
:envvar:`ldap/server/addition`.

The :term:`UCR variable` :envvar:`nssldap/bindpolicy`
controls how the module behaves
when the LDAP server is unavailable.
By default, the module tries to connect again.
If you set the variable to ``soft``,
the module doesn't try again.
This setting improves system boot performance
in an isolated test environment.

.. _domain-infrastructure-ldap-directory-samba-4:

Configuration of the directory service when using Samba/AD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the OpenLDAP server accepts requests on ports ``7389`` and ``7636``
in addition to the standard ports ``389`` and ``636``.

If you use Samba/AD,
the Samba/AD domain controller service occupies ports ``389`` and ``636``.
In that case, OpenLDAP uses only ports ``7389`` and ``7636``.
:command:`univention-ldapsearch` uses the standard port automatically.

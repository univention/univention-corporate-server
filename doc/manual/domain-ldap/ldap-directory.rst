.. _domain-ldap:

LDAP directory
==============

.. highlight:: console

Univention Corporate Server saves domain-wide data in a LDAP directory service
based on OpenLDAP. This chapter describes the advanced configuration and
coordination of OpenLDAP.

Often several LDAP servers are operated in a UCS domain. The configuration of
the server(s) used is described in :ref:`computers-configure-ldap-server`.

.. _domain-ldap-schema:

LDAP schemas
------------

Schema definitions specify which object classes exist and which attributes they
include, i.e., which data can be stored in a directory service. Schema
definitions are saved as text files and included in the OpenLDAP server's
configuration file.

UCS uses standard schemas where possible in order to allow interoperability with
other LDAP applications. Schema extensions are supplied for Univention-specific
attributes - such as for the policy mechanism.

.. _domain-ldap-extensions:

LDAP schema extensions
~~~~~~~~~~~~~~~~~~~~~~

To keep the efforts required for small extensions in LDAP as low as possible,
|UCSUCS| provides its own LDAP scheme for customer extensions. The LDAP object
class ``univentionFreeAttributes`` can be used for extended attributes without
restrictions. It offers 20 freely usable attributes
(``univentionFreeAttribute1`` to ``univentionFreeAttribute20``) and can be used
in connection with any LDAP object (e.g., a user object).

If LDAP schema extensions are to be delivered as part of software packages,
there is also the possibility of packaging them and distributing them to all the
|UCSBACKUPDN| servers in the domain using a |UCSUDL| module. Further information
is available in :ref:`settings-ldapschema`.

.. _domain-ldap-schema-replication:

LDAP schema replication
~~~~~~~~~~~~~~~~~~~~~~~

The replication of the LDAP schemas is also automated via the listener/notifier
mechanism (see :ref:`domain-listener-notifier`). This relieves the administrator
of the need to perform all schema updates manually on all the OpenLDAP servers
in the domain. Performing the schema replication before the replication of LDAP
objects guarantees that this doesn't fail as a result of missing object classes
or attributes.

On the |UCSPRIMARYDN|, a checksum for all the directories with schema
definitions is performed when the OpenLDAP server is started. This checksum is
compared with the last saved checksum in the
:file:`/var/lib/univention-ldap/schema/md5` file.

The actual replication of the schema definitions is initiated by the
|UCSUDL|. Prior to every request from the |UCSUDN| for a new transaction ID,
its current schema ID is requested. If this is higher than the schema ID
on the listener side, the currently used sub-schema is procured from the
notifier system's LDAP server via an LDAP search.

The output sub-schema is included on the listener system in LDIF format in the
:file:`/var/lib/univention-ldap/schema.conf` file and the local OpenLDAP server
restarted. If the schema replication is completed with this step, the
replication of the LDAP objects is continued.

.. _domain-ldap-directory-logger:

Audit-proof logging of LDAP changes
-----------------------------------

The :program:`univention-directory-logger` package allows the logging of all
changes in the LDAP directory service. As each data record contains the hash
value of the previous data record, manipulations of the log file - such as
deleted entries - can be uncovered.

Individual areas of the directory service can be excluded from the logging.
These branches can be configured using the |UCSUCR| variables
:envvar:`ldap/logging/exclude1`, :envvar:`ldap/logging/excludeN`, etc. As standard, the
container is excluded in which the temporary objects are stored
(``cn=temporary,cn=univention``). The LDAP changes are logged by a |UCSUDL|
module. The |UCSUDL| service must be restarted if changes are made to the
|UCSUCR| variables.

The logging is made in the
:file:`/var/log/univention/directory-logger.log` file in the following format:

.. code-block:: none

   START
   Old Hash: Hash sum of the previous data record
   DN: DN of the LDAP object
   ID: Listener/notifier transaction ID
   Modifier: DN of the modifying account
   Timestamp: Time stamp in format dd.mm.yyyy hh:mm:ss
   Action: add, modify or delete

   Old Values:
    List of old attributes, empty when an object is added
   New Values:
    List of new attributes, empty when an object is deleted
   END


A hash sum is calculated for each logged data record and also logged in the
``daemon.info`` section of the syslog service.

As of :uv:erratum:`4.4x536` the respective transaction ID of the entry is
added to the file :file:`/var/log/univention/directory-logger.log` before each
line as a prefix:

.. code-block:: none

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


If :program:`univention-directory-logger` was installed before this UCS version,
the old behavior (no prefix) is retained by default. By setting the |UCSUCRV|
:envvar:`ldap/logging/id-prefix` to ``yes`` the new behavior can be activated.
This prefix simplifies the correlation of related lines when post-processing the
sign in analysis and monitoring software.

.. _domain-ldap-timeout-for-inactive-ldap-connections:

Timeout for inactive LDAP connections
-------------------------------------

The |UCSUCRV| :envvar:`ldap/idletimeout` is used to configure a time period in
seconds after which the LDAP connection is cut off on the server side. When the
value is set to ``0``, no expiry period is in use. The timeout period has been set
at six minutes as standard.

.. _domain-ldap-command-line-tools:

LDAP command line tools
-----------------------

In addition to the UMC web interface, there are also a range of programs with
which one can access the LDAP directory from the command line.

The :command:`univention-ldapsearch` tool simplifies the authenticated search in
the LDAP directory. A search filter needs to be specified as an argument; in the
following example, the administrator is searched for using the user ID:

.. code-block::

   $ univention-ldapsearch uid=Administrator


The :command:`slapcat` command makes it possible to save the current LDAP data
in a text file in LDIF format, e.g.:

.. code-block::

   $ slapcat > ldapdata.txt


.. _domain-ldap-acls:

Access control for the LDAP directory
-------------------------------------

Access to the information contained in the LDAP directory is controlled by
Access Control Lists (ACLs) on the server side. The ACLs are defined in the
central configuration file :file:`/etc/ldap/slapd.conf` and managed using
|UCSUCR|.

The :file:`slapd.conf` is managed using a multifile template; further ACL
elements can be added below
:file:`/etc/univention/templates/files/etc/ldap/slapd.conf.d/` between the
:file:`60univention-ldap-server_acl-master` and
:file:`70univention-ldap-server_acl-master-end` files or the existing templates
expanded upon.

If LDAP ACL extensions are to be delivered as part of software packages, there
is also the possibility of packaging them and distributing them to all the LDAP
servers in the domain using a |UCSUDL| module. Further information is available
in :ref:`settings-ldapacl`.

The default setting of the LDAP server after new installations with UCS
does not allow anonymous access to the LDAP directory. This behavior is
configured with the |UCSUCRV| :envvar:`ldap/acl/read/anonymous`.
Individual IP addresses can be granted anonymous read permissions via
|UCSUCRV| :envvar:`ldap/acl/read/ips`.

Following successful authentication on the LDAP server, all attributes of a user
account can be read out by this user.

In addition, an extra, internal account, the root DN, also has full write
access.

In addition, UCS offers a number of further ACLs installed as standard
which suppress access to sensitive files (e.g., the user password) and
establish rules which are necessary for operation (e.g., necessary
accesses to computer accounts for log-ins). The read and write access to
this sensitive information if only intended for members of the
``Domain Admins`` group.

Nested groups are also supported. The |UCSUCRV| :envvar:`ldap/acl/nestedgroups`
can be used to deactivate the nested groups function for LDAP ACLs, which will
result in a speed increase for directory requests.

.. _domain-ldap-delegation-of-the-priviledge-to-reset-user-passwords:

Delegation of the privilege to reset user passwords
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To facilitate the delegation of the privilege to reset user passwords, the
:program:`univention-admingrp-user-passwordreset` package can be installed. It
uses a join script to create the ``User Password Admins`` user group, in so far
as this does not already exist.

Members of this group receive the permission via additional LDAP ACLs to reset
the passwords of other users. These LDAP ACLs are activated automatically during
the package installation. To use another group, or a group that already exists,
instead of the ``User Password Admins`` group, the DN of the group to be used
can be entered in the |UCSUCRV|
:envvar:`ldap/acl/user/passwordreset/accesslist/groups/dn`. The LDAP server must
be restarted after making changes.

Passwords can be reset via the UMC module :guilabel:`Users`. By default the
module is only accessible to the ``Administrator`` user. During the installation
a new ``default-user-password-admins`` policy is created automatically, which is
linked to the members of the ``User Password Admins`` group and can be assigned
to a corresponding container in the LDAP directory. Further information on the
configuration of UMC policies can be found in :ref:`delegated-administration`.

The policy makes it possible to search for users and create an overview of all
the attributes of a user object. If an attempt is made to modify further
attributes in addition to the password when the user does not have sufficient
access rights to the LDAP directory, |UCSUDM| denies them write access with the
message *Permission denied*.

.. caution::

   The package should be installed on the |UCSPRIMARYDN| and the
   |UCSBACKUPDN|\ s. During the installation, the LDAP server is restarted
   and is thus temporarily unavailable.

Password resets via the password group can be prevented for sensitive users or
groups (e.g., domain administrators). The |UCSUCR| variables
:envvar:`ldap/acl/user/passwordreset/protected/uid` and
:envvar:`ldap/acl/user/passwordreset/protected/gid` can be used to configure
users and groups. Multiple values must be separated by commas. After changes to
the variables, it is necessary to restart the LDAP server using the
:command:`systemctl restart slapd` command. By default the members of the
``Domain Admins`` group are protected against having theirs password changed.

If access to additional LDAP attributes should be necessary for changing the
password, the attribute names can be expanded in |UCSUCRV|
:envvar:`ldap/acl/user/passwordreset/attributes`. After the change, the LDAP
directory service must be restarted for the change to take effect. This variable
is already set appropriately for a UCS standard installation.

.. _domain-ldap-name-service-switch-ldap-nss-module:

Name Service Switch / LDAP NSS module
-------------------------------------

With the *Name Service Switch*, the GNU C standard library (:program:`glibc`)
used in Univention Corporate Server offers a modular interface for resolving the
names of users, groups and hosts.

The LDAP NSS module is used on UCS systems for access to the domain data
(e.g., users) as standard. The module queries the LDAP server specified
in the |UCSUCRV| :envvar:`ldap/server/name` (and if necessary the
:envvar:`ldap/server/addition`).

What measures should be taken if the LDAP server cannot be reached can be
specified by the |UCSUCRV| :envvar:`nssldap/bindpolicy`. As standard, if the
server cannot be reached, a new connection attempt is made. If the variable is
set to ``soft``, then no new attempt is made to connect. This can considerably
accelerate the boot of a system if the LDAP server cannot be reached, e.g., in
an isolated test environment.

.. _domain-ldap-syncrepl:

Syncrepl for synchronization with non-UCS OpenLDAP servers
----------------------------------------------------------

The syncrepl replication service can also be activated parallel to the
notifier service for the synchronization of OpenLDAP servers not
installed on UCS systems. Syncrepl is a component of OpenLDAP, monitors
changes in the local directory service and transmits them to other
OpenLDAP servers.

.. _domain-ldap-configuration-of-the-directory-service-when-using-samba-4:

Configuration of the directory service when using Samba/AD
----------------------------------------------------------

As standard, the OpenLDAP server is configured in such a way that it also
accepts requests from ports ``7389`` and ``7636`` in addition to the standard
ports ``389`` and ``636``.

If Samba/AD is used, the Samba/AD domain controller service occupies the ports
``389`` and ``636``. In this case, OpenLDAP is automatically reconfigured so
that only ports ``7389`` and ``7636`` are used. This must be taken into account
during the configuration of syncrepl in particular (see
:ref:`domain-ldap-syncrepl`). :command:`univention-ldapsearch` uses the
standard port automatically.

.. _domain-ldap-nightly-backup:

Daily backup of LDAP data
-------------------------

The content of the LDAP directory is backed up daily on the |UCSPRIMARYDN|
and all |UCSBACKUPDN| systems via a Cron job. If Samba 4 is used, its data
directory is also backed up.

The LDAP data are stored in the :file:`/var/univention-backup/` directory in the
naming scheme :file:`ldap-backup_DATE.ldif.gz` in LDIF
format. They can only be read by the ``root`` user. The Samba 4 files are stored in
the directory :file:`/var/univention-backup/samba/`.

The |UCSUCRV| :envvar:`backup/clean/max_age` can be used to define how long old
backup files are kept (e.g. ``backup/clean/max_age=365``, all files older than
``365`` days are automatically deleted). For new installations (from UCS 4.4-7
on) the default for this variable is ``365`` (days). If the variable is not set,
no backup files are deleted.

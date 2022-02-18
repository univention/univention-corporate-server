.. _connection-idm:

Connection with Identity Management
===================================

One of the key features of UCS is the integrated identity management
(IDM). With this central identity management, users benefit, among other
things, from a single login independent of which services or systems
they use. It is highly recommended to integrate the app into the
identity management system.

If the app should benefit from the identity management, the flag :guilabel:`The
administrator needs to enable users for the app` should be activated in
the App Provider Portal on the :guilabel:`Identity management` tab under the *User
rights management* section. This extends the IDM by a checkbox and an
administrator of the UCS system can activate or deactivate each user
individually for the app. The setting can then be found in the Users UMC
module and is called :guilabel:`Apps`. It is also possible to make significantly
more complex settings. See :ref:`User rights
management <user-rights-management>` for more details.

Provisioning
------------

There are different ways in which applications can access provisioning
information. The following describes a pull and push-based procedure.

.. _provisioning:pull:

Automatically via LDAP connection (Pull)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

UCS stores the user and group information in an OpenLDAP based
directory. Thus, the default information can be accessed via the LDAP
protocol. Objects are identified by an LDAP filter. The following filter
can be used to search for users ``(univentionObjectType=users/user)``
and for groups the filter ``(univentionObjectType=groups/group)`` can be
used.

If the user activation is used (:guilabel:`The administrator needs to enable users
for the app`), the following LDAP filter can be used:
``(&(univentionObjectType=users/user)(myappActivated=TRUE))``. The string
``myapp`` has to be replaced with the *appid*.

The parameters for the LDAP server can be read from the environment
variables:

``LDAP_SERVER_NAME``
   The fully-qualified host name of the OpenLDAP server the app may
   connect to.

``LDAP_SERVER_PORT``
   The port of the OpenLDAP server the app may connect to.

``LDAP_SERVER_ADDITION``
   A list of alternative OpenLDAP servers. These values should be used
   for failover.

``LDAP_BASE``
   The base for the whole LDAP database, e.g.,
   ``dc=mydomain,dc=intranet`` or ``o=mydomain <o=mydomain>``.

.. important::

   As a rule, the LDAP base should not be further restricted. Many
   environments store users below ``cn=users <cn=users>`` but this is
   not the case in all environments.

By default, the OpenLDAP server in UCS does not allow anonymous
connections. For every app a user account is created. The account has
read access to the LDAP directory. The username is passed as the
environment variable ``LDAP_HOSTDN``. The password is written in the file
:file:`/etc/machine.secret`. The credentials are not changed when an app is
upgraded. But they change if an app is reinstalled.

.. _provisioning:push:

Automatically via IDM notifications (Push)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An app can be notified by the IDM system when users or groups are
created, modified or deleted. For each change, a file is created in a
specific directory. The app can either poll the directory or register a
command that is executed when a file is created.

211 is required on the user's system for this feature.

.. _provision:push:setup:

Setup in App configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

The configuration for these IDM notifications can be done on the
:guilabel:`Identity management` tab in the *Provisioning* section in the App Provider
Portal. It can be configured which object types are watched. Currently,
users and groups are supported.

A script should be specified in the App Provider Portal. The script is
copied from the App Center into the Docker container and executed in the
context of the container there. If a script is already part of the
container, this script can be called accordingly, e.g.

.. code:: sh

   #/bin/sh
   /usr/sbin/app-connector

.. _provision:push:mechanism:

How the mechanism works
^^^^^^^^^^^^^^^^^^^^^^^

The JSON files are created in the directory
:file:`/var/lib/univention-appcenter/apps/$appid/data/listener/`. As soon as
any attribute of the watched object types is changed a JSON file is
created in the directory. The script is called in a defined and
configurable interval by the App Center, if at least one JSON file has
been written. Once the script has finished a JSON file, the script must
delete the JSON file.

All files are JSON with one dictionary and the following content:

``id``
   A unique identifier for the object holding the value of
   ``entry_uuid`` attribute of the LDAP object. It does not change even
   if the object is moved. The script certainly wants to identify
   objects by this attribute.

``dn``
   The distinguished name of the LDAP object.

``type``
   The type of the object, i.e., "users/user", or "groups/group".

``attributes``
   A dictionary of the attributes of this object. The
   content is defined by the UDM (Univention Directory Manager)
   representation of the object. If it is null instead, the object has
   been deleted.

Logging information about the listener can found in
:file:`/var/log/univention/listener_modules/$appid.log`.

.. _provision:push:script:

What should the script cover?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* The mechanism does not filter the data. Every change will be saved in
  JSON files. If only a subset of users, e.g. a certain user type like
  students, shall be processed, the script should filter on it and only
  continue with the relevant data.

* UCS can re-synchronize a listener. In this case, each and every
  object appears once again as a JSON file. The script needs to cover
  the case where no real modification to the object has been made.

* The script has to exit with exit code = 0 on success and != 0 on
  failure.

* The script has to delete the JSON file that has already been
  processed. If the files are not deleted, the script should detect
  duplicates and make sure to handle the same change accordingly.

* If a mapping between the ``id`` of the JSON file and the primary user
  key in the solutions database is not possible, consider maintaining a
  mapping table by the script, if necessary. The ``id`` is the only
  attribute that remains the same for an object.

* It may happen that the same ``id`` appears twice in the set of JSON
  files. This means that multiple modifications on the object have been
  made since the last time your script processed the object.

.. _provision:push:json:

JSON example
^^^^^^^^^^^^

This is an example of a JSON file for a user change. It is not complete,
but should clarify the idea.

.. code:: js

   {
       "dn": "uid=Administrator,cn=users,dc=sparka-43,dc=intranet",
       "id": "b2f13544-e3cb-1037-810e-23ad4765aade",
       "object": {
           "description": "Built-in account for administering the computer/domain",
           "disabled": "0",
           "displayName": "Administrator",
           "gecos": "Administrator",
           "gidNumber": "5000",
           "groups": [
               "cn=Domain Admins,cn=groups,dc=sparka-43,dc=intranet",
               "cn=Domain Users,cn=groups,dc=sparka-43,dc=intranet",
               "cn=DC Backup Hosts,cn=groups,dc=sparka-43,dc=intranet",
               "cn=Schema Admins,cn=groups,dc=sparka-43,dc=intranet",
               "cn=Enterprise Admins,cn=groups,dc=sparka-43,dc=intranet",
               "cn=Group Policy Creator Owners,cn=groups,dc=sparka-43,dc=intranet",
               "cn=Administrators,cn=Builtin,dc=sparka-43,dc=intranet"
           ],
           "lastname": "Administrator",
           "locked": "0",
           "lockedTime": "0",
           "mailForwardCopyToSelf": "0",
           "mailPrimaryAddress": "admin@sparka-43.intranet",
           "mailUserQuota": "0",
           "password": "{crypt}$6$0kS4GowCZEAJRqWG$8LkK6iBeKFCInoxy9bCG1SFfGpajOy//Zg[...]",
           "passwordexpiry": null,
           "primaryGroup": "cn=Domain Admins,cn=groups,dc=sparka-43,dc=intranet",
           "sambaRID": "500",
           "shell": "/bin/bash",
           "uidNumber": "2002",
           "umcProperty": [
               [
                   "appcenterDockerSeen",
                   "true"
               ],
               [
                   "appcenterSeen",
                   "2"
               ],
               [
                   "udmUserGridView",
                   "default"
               ]
           ],
           "unixhome": "/home/Administrator",
           "unlockTime": "",
           "userexpiry": null,
           "username": "Administrator",
           "webweaverActivated": "TRUE"
       },
       "udm_object_type": "users/user"
   }

Authentication
--------------

There are different ways in which applications can authenticate against
the UCS identity management system.

.. _authentication:ldap:

LDAP
~~~~

UCS stores the user and group information in an OpenLDAP based
directory. Thus, the default information can be accessed via the LDAP
protocol. Objects are identified by an LDAP filter. The following filter
can be used to search for users ``(univentionObjectType=users/user)``
and for groups the filter ``(univentionObjectType=groups/group)`` can be
used.

If the user activation is used (The administrator needs to enable users
for the app), the following LDAP filter can be used:
``(&(univentionObjectType=users/user)(myappActivated=TRUE))``. The
string ``myapp`` has to be replaced with the *appid*.

The parameters for the LDAP server can be read from the environment
variables:

``LDAP_SERVER_NAME``
   The fully-qualified host name of the OpenLDAP server the app may
   connect to.

``LDAP_SERVER_PORT``
   The port of the OpenLDAP server the app may connect to.

``LDAP_SERVER_ADDITION``
   A list of alternative OpenLDAP servers. These values should be used
   for failover.

``LDAP_BASE``
   The base for the whole LDAP database, e.g.,
   ``dc=mydomain,dc=intranet`` or
   ``o=mydomain <o=mydomain>``.

.. important::

   As a rule, the LDAP basis should not be further restricted. Many
   environments store users below ``cn=users <cn=users>`` but this is
   not the case in all environments.

By default, the OpenLDAP server in UCS does not allow anonymous
authentications. For every app a user account is created. The account
has read access to the LDAP directory. The username is passed as the
environment variable ``LDAP_HOSTDN``. The password is written in the file
:file:`/etc/machine.secret`. The credentials are not changed when an app is
upgraded. But they change if an app is reinstalled.

.. _authentication:kerberos:

Kerberos
~~~~~~~~

UCS integrates a Kerberos server by default. As usual with Kerberos, the
data for the Kerberos configuration can be obtained from DNS. By
default, the DNS domain name is passed through the ``DOMAINNAME``
environment variable. The following settings can then be queried via
DNS:

Kerberos Realm
   It an be queried by the TXT record ``\_kerberos.DOMAINNAME``.

Kerberos KDC
   It an be queried by the SRV records ``\_kerberos._tcp.DOMAINNAME and \_kerberos._udp.DOMAINNAME``.

.. _user-rights-management:

User rights management
----------------------

The flag :guilabel:`The administrator needs to enable users for the app` can be
activated in the App Provider Portal on the :guilabel:`Identity management` tab in
the *User rights management* section. This adds a checkbox to the user
administration and a schema extension for the IDM is created, so that
the status of the checkbox is stored in an attribute in the IDM. This
allows each user to be activated or deactivated separately.

If the app requires more settings in the IDM, an own LDAP schema can be
uploaded into the App Provider Portal on the :guilabel:`Identity management` tab in
the *User rights management* section in the field *Schema extension for
LDAP*.

In this case, it is also possible to create individual extended
attributes during the setup process. This should be done in the join
script. Further information on extended attributes can be found in the
`Univention Developer Reference <univention-dev-reference_>`_.

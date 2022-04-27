.. _ip-config-radius:

RADIUS
======

The :program:`RADIUS` app increases the security for UCS managed IT
infrastructures by controlling the access to the wireless network for users,
groups and endpoint devices via `RADIUS protocol <w-radius_>`_. The
configuration is done via deny and allow lists and directly at user, group and
endpoint device objects in the UCS management system. Registered users are
authenticated with their usual domain credentials or, alternatively, with a
specifically for RADIUS generated password, which, among others, also allows
bring your own device concepts.

.. _ip-config-radius-installation:

Installation
------------

:program:`RADIUS` is available through the App Center (see
:ref:`software-appcenter`) and can be installed using the UMC module
:guilabel:`App Center`. It can be installed on multiple machines. After the
installation it runs a `FreeRADIUS <freeradius_>`_ server.
Authenticators (e.g.  access points) can contact via RADIUS to check network
access requests.

The RADIUS app can also be installed on UCS\@school systems. In this case, the
network access can be given to users or groups regardless of the internet rule
or computer room settings.

.. _ip-config-radius-configuration:

Configuration
-------------

.. _ip-config-radius-configuration-allowed-users:

Allowed users
~~~~~~~~~~~~~

By default no user is allowed to access the network. Enabling the checkbox for
*network access* on the *RADIUS* tab, gives the user access to the network. The
checkbox can also be set on groups, which allows all users in this group access.

.. _ip-config-radius-group:

.. figure:: /images/radius-group-allow-network.*
   :alt: Example for a group allowing network access to its users

   Example for a group allowing network access to its users

.. _ip-config-radius-configuration-service-specific-password:

Service specific password
~~~~~~~~~~~~~~~~~~~~~~~~~

By default, users authenticate with their domain password. By setting the
|UCSUCRV| :envvar:`radius/use-service-specific-password` to ``true``, a dedicated
password for RADIUS will be used. Through the :ref:`Self Service app
<user-management-password-changes-by-users>`, users can get such a password. The
system will generate a random password for users to use. If needed, a new
password can be generated at any time. This also invalidates the old password.
To enable this page in the Self Service, the |UCSUCRV|
:envvar:`umc/self-service/service-specific-passwords/backend/enabled` has to be
set to ``true`` on the :guilabel:`Self Service Backend`.

.. _ip-config-radius-selfservice:

.. figure:: /images/radius-service-specific-password.*
   :alt: The page in the Self Service to get a RADIUS specific password

   The page in the Self Service to get a RADIUS specific password

The parameters used to generate the passwords can be adjusted. On a
|UCSPRIMARYDN| some |UCSUCRV|\ s have to be set:

.. code-block:: console

   $ ucr search password/radius/quality


.. _ip-config-radius-configuration-mac-filtering:

MAC filtering
~~~~~~~~~~~~~

By default access to the network is allowed for every device (assuming the used
username has access). It can be restricted to only allow specific devices. This
can be enabled by setting the |UCSUCRV| :envvar:`radius/mac/whitelisting` to
``true``. When enabled, the device used to access the network is looked up via
the LDAP attribute ``macAddress`` and the resulting computer object must have
network access granted (either directly or via one of its groups), too.

.. _ip-config-radius-configuration-access-points-registration:

Access point administration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

All access points must be known to the RADIUS server. An access point can either
be configured in the file :file:`/etc/freeradius/3.0/clients.conf` or through
the UMC module :guilabel:`Computers`. For each access point a random shared
secret should be created (e.g. by using the command :command:`makepasswd`). The
``shortname`` can be chosen at will.

Example entry for an access point:

.. code-block::

   client AP01 {
       secret = a9RPAeVG
       ipaddr = 192.0.2.101
   }

To configure an access point using the UMC module :guilabel:`Computers` create
or select a computer object and activate the *RADIUS-Authenticator* option
(:ref:`ip-config-radius-option`). An *IP client* is a good choice as a computer
object for access points. The RADIUS settings can be edited on the *RADIUS* tab
of the object (:ref:`ip-config-radius-authenticator`). At least the IP address
and the shared secret must be configured. The virtual server and NAS type
options usually do not need to be changed.

Access points that are configured via the UMC module :guilabel:`Computers` are
available to all RADIUS servers in the domain. To achieve this, the |UCSUDL|
will write them into the file
:file:`/etc/freeradius/3.0/clients.univention.conf` and restart the RADIUS
server. In order to merge multiple changes in one restart, this happens with a
slight delay (around 15 seconds). New access points can only access the RADIUS
server after this restart.

.. _ip-config-radius-option:

.. figure:: /images/radius_option.*
   :alt: RADIUS option

   RADIUS option

.. _ip-config-radius-authenticator:

.. figure:: /images/radius_authenticator.*
   :alt: RADIUS authenticator options

   RADIUS authenticator options

.. _ip-config-radius-configuration-access-points-clients:

Access point and client configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The access points must then be configured to use 802.1x ("WPA Enterprise")
authentication. And the *RADIUS server* address should be set to the address of
the server, where the RADIUS app is installed. The password must be set to the
``secret`` from the :file:`clients.conf` entry for that access point.

Wireless clients have to be configured to use *WPA* with *PEAP* and *MSCHAPv2* for
authentication.

.. _ip-config-radius-configuration-vlanid-configuration:

VLAN IDs
~~~~~~~~

Virtual Local Area Networks (VLANs) can be used to separate the traffic of users at
the network level. UCS can be configured to return a VLAN-ID in the Radius response
of the Radius authentication process according to RFC 3580 / IEEE 802.1X.

The VLAN-ID for a user can be configured by assigning the user to a group with a VLAN-ID.

.. _radius-vlanid-group:

.. figure:: /images/radius-vlanid-group.*
   :alt: Assigning VLAN ID to a user group

   Assigning VLAN ID to a user group

A default VLAN-ID can be configured in the |UCSUCRV| :envvar:`freeradius/vlan-id`. This default
VLAN-ID will be returned if the user is not a member of a group with a VLAN-ID. The Radius
response will not contain any VLAN-ID in case the user is not a member of a group with
VLAN-ID and no default VLAN-ID is defined.

.. _ip-config-radius-debugging:

Debugging
---------

The :program:`RADIUS` app has a log file under
:file:`/var/log/univention/radius_ntlm_auth.log`. The log verbosity can the
controlled via the |UCSUCRV| :envvar:`freeradius/auth/helper/ntlm/debug`. The
:program:`FreeRADIUS server` uses the log file:
:file:`/var/log/freeradius/radius.log`.

The tool :program:`univention-radius-check-access` can be used to evaluate the
current access policy for a given user and/or station ID (MAC address). It can
be executed as root on the server where :program:`univention-radius` its
installed:

.. code-block:: console

   root@primary211:~# univention-radius-check-access --username=stefan
   DENY 'uid=stefan,cn=users,dc=ucs,dc=local'
   'uid=stefan,cn=users,dc=ucs,dc=local'
   -> DENY 'cn=Domain Users,cn=groups,dc=ucs,dc=local'
   -> 'cn=Domain Users,cn=groups,dc=ucs,dc=local'
   -> -> DENY 'cn=Users,cn=Builtin,dc=ucs,dc=local'
   -> -> 'cn=Users,cn=Builtin,dc=ucs,dc=local'
   Thus access is DENIED.

.. code-block:: console

   root@primary211:~# univention-radius-check-access --username=janek
   DENY 'uid=janek,cn=users,dc=ucs,dc=local'
   'uid=janek,cn=users,dc=ucs,dc=local'
   -> DENY 'cn=Domain Users,cn=groups,dc=ucs,dc=local'
   -> ALLOW 'cn=Network Access,cn=groups,dc=ucs,dc=local'
   -> 'cn=Domain Users,cn=groups,dc=ucs,dc=local'
   -> -> DENY 'cn=Users,cn=Builtin,dc=ucs,dc=local'
   -> -> 'cn=Users,cn=Builtin,dc=ucs,dc=local'
   -> 'cn=Network Access,cn=groups,dc=ucs,dc=local'
   Thus access is ALLOWED.
   root@primary211:~#

It prints a detailed explanation and sets the exit code depending on the result
of the access check (``0`` for *access granted*, ``1`` for *access denied*).

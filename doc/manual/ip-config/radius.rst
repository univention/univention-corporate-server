.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

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

.. _ip-config-radius-configuration-mab:

MAC Authentication Bypass with computer objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MAC Authentication Bypass (MAB) is a proprietary fallback mode to 802.1X
for devices that don't support 802.1X authentication,
such as network printers or wireless phones.
MAB is an option that allows such devices to authenticate with the network
using their MAC address as their username.

This section describes how to use a device's MAC address for authentication
and assign them a VLAN to the corresponding network infrastructure through MAB.
To activate MAC Authentication Bypass, set the |UCSUCRV|
:envvar:`freeradius/conf/allow-mac-address-authentication` to ``true``.

.. important::

   Devices that authenticate using MAB ignore network access settings:

   * |UCSUCRV| :envvar:`radius/mac/whitelisting`

   * The checkbox *Allow network access* at the computer object and in the group setting

.. warning::

   Attackers can spoof MAC addresses.
   Consider any port as compromised where your switch allows to use MAB.
   Make sure you have put appropriate measures in place to still keep your network secure.

.. tab:: Assign VLAN ID to computer

   To assign the VLAN ID to a computer,
   you need to add it to the group of the computer object with the respective VLAN ID.
   In the UCS management system, follow these steps:

   #. Open :menuselection:`Devices --> Computers`.

   #. Click the computer object to edit.

   #. Go to :menuselection:`Advanced settings --> Groups`.

   #. To add a group with VLAN IDs, click :guilabel:`+ ADD`,
      select ``Virtual LAN ID`` from the *Object property* drop-down,
      and activate the appropriate group to add it.

   #. To save, click :guilabel:`ADD` in the *Add objects* dialog
      and :guilabel:`SAVE` in the *Advanced settings*.

.. tab:: Assign VLAN ID to user group

   To assign the VLAN ID to a user group, you need to add it to the user group settings.
   In the UCS management system, follow these steps:

   #. Open :menuselection:`Users --> Groups`.

   #. Click the user group object to edit or create a new user group.

   #. Go to :menuselection:`RADIUS`.

   #. Enter the VLAN ID as number into the field *Virtual LAN ID*.

   #. To save, click :guilabel:`SAVE`.

If a computer object has assigned several groups with VLAN IDs,
UCS selects the VLAN ID with the lowest number and assigns it.
To configure a default VLAN ID, set it as value to the |UCSUCRV|
:envvar:`freeradius/vlan-id`.

After you completed the configuration,
the Radius server returns the assigned VLAN ID to requests with the given MAC address.

.. important::

   You must provide the MAC address in the correct format. UCS stores the MAC
   address in the LDAP directory as lowercase string with the colon (``:``) as
   separator, for example ``00:00:5e:00:53:00``.

   All devices that use MAB, need to have the same password set,
   because :ref:`service specific passwords <ip-config-radius-configuration-service-specific-password>` don't work,
   and the switch must know the password.
   You can only configure one device password in the switch.
   You can make up your own password for the devices using MAB,
   for example ``mab request format attribute 2 password1``.

   If the network infrastructure provides a different format,
   you can often reconfigure the format.
   For example, for Cisco switches, you can use ``mab request format attribute 1 groupsize 2 separator : lowercase``
   as described in
   `Configurable MAB Username and Password
   <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_usr_aaa/configuration/15-e/sec-usr-aaa-15-e-book/sec-usr-config-mab-usrname-pwd.html>`_.


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

Virtual Local Area Networks (VLANs) can be used to separate the traffic of users
at the network level. UCS can be configured to return a VLAN ID in the Radius
response of the Radius authentication process according to :rfc:`RFC 3580 / IEEE 802.1X
<3580>`. You find further information in :ref:`computers-network-complex-vlan`.

The VLAN ID for a user can be configured by assigning the user to a group with a VLAN ID.

.. _radius-vlanid-group:

.. figure:: /images/radius-vlanid-group.*
   :alt: Assigning VLAN ID to a user group

   Assigning VLAN ID to a user group

A default VLAN ID can be configured in the |UCSUCRV| :envvar:`freeradius/vlan-id`. This default
VLAN ID will be returned if the user is not a member of a group with a VLAN ID. The Radius
response will not contain any VLAN ID in case the user is not a member of a group with
VLAN ID and no default VLAN ID is defined.

.. _ip-config-radius-disable-tls-1-3:

Disable TLS 1.3
~~~~~~~~~~~~~~~

Radius uses Transport Layer Security (TLS) to encrypt web traffic.
The current version of all major operating systems supports TLS 1.3.
Some operating systems, such as Microsoft Windows 10, have issues with the Radius implementation used.
For detailed information, see :uv:bug:`55247`.

If you still use those, you might have to to disable TLS v1.3.
To limit TLS to version 1.2,
change the |UCSUCRV| :envvar:`freeradius/conf/tls-max-version` to the value ``1.2``.

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
   DENY 'uid=stefan,cn=users,dc=ucs,dc=example'
   'uid=stefan,cn=users,dc=ucs,dc=example'
   -> DENY 'cn=Domain Users,cn=groups,dc=ucs,dc=example'
   -> 'cn=Domain Users,cn=groups,dc=ucs,dc=example'
   -> -> DENY 'cn=Users,cn=Builtin,dc=ucs,dc=example'
   -> -> 'cn=Users,cn=Builtin,dc=ucs,dc=example'
   Thus access is DENIED.

.. code-block:: console

   root@primary211:~# univention-radius-check-access --username=janek
   DENY 'uid=janek,cn=users,dc=ucs,dc=example'
   'uid=janek,cn=users,dc=ucs,dc=example'
   -> DENY 'cn=Domain Users,cn=groups,dc=ucs,dc=example'
   -> ALLOW 'cn=Network Access,cn=groups,dc=ucs,dc=example'
   -> 'cn=Domain Users,cn=groups,dc=ucs,dc=example'
   -> -> DENY 'cn=Users,cn=Builtin,dc=ucs,dc=example'
   -> -> 'cn=Users,cn=Builtin,dc=ucs,dc=example'
   -> 'cn=Network Access,cn=groups,dc=ucs,dc=example'
   Thus access is ALLOWED.
   root@primary211:~#

It prints a detailed explanation and sets the exit code depending on the result
of the access check (``0`` for *access granted*, ``1`` for *access denied*).

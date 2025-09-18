.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _ucs-operation-groups:

*****************
Groups management
*****************

.. TODO: Add an introduction. Refer to the general chapter about group management in the Nubus Manual.



In addition, there are also local user groups on each system, which are
predominantly used for hardware access. These are not managed through the
*Management UI*, but saved in the :file:`/etc/group` file.

.. _ucs-operation-groups-management:

Managing groups through management module
=========================================

For a complete reference of the *Group* management module,
see :external+uv-nubus-manual:ref:`nubus-groups-management`.

This section amends the reference with specifics
that apply to the UCS appliance.

.. _ucs-operation-groups-management-tab-general-name:

:menuselection:`General tab --> Name`
   For the reference,
   see :external+uv-nubus-manual:ref:`nubus-groups-management-tab-general-name`.

   By default, it isn't possible to create a group
   with the same name as an existing user.
   If the UCR variable
   :envvar:`directory/manager/user_group/uniqueness` has the value  ``false``,
   Nubus doesn't run this check.

.. _ucs-operation-groups-management-tab-advanced-field-group-type:

:menuselection:`Advanced settings tab --> Windows --> group type`

nubus-groups-management-tab-advanced-field-group-type
   For the reference,
   see :external+uv-nubus-manual:ref:`nubus-groups-management-tab-advanced-field-group-type`.

   Local groups
      See the reference for the description.

      If a local group is created on a Windows server,
      solely the server knows this group.
      A local group isn't available across the domain.
      In contrast, the UCS appliance doesn't differentiate between local and global groups.
      After taking over an AD domain,
      the UCS appliance handles local groups in the same way as *Domain Groups*.


.. _ucs-operation-groups-management-nested:

Group nesting with groups in groups
===================================

For a description,
see :external+uv-nubus-manual:ref:`nubus-groups-management-nested`.

Nubus runs a plausibility check
to detect cyclic dependencies in nested groups.
To deactivate this check, set the UCR variable
:envvar:`directory/manager/web/modules/groups/group/checks/circular_dependency`
to the value ``no``.
The default value is ``yes``.
If you don't use the *Management UI* for group changes,
you must avoid cyclic memberships in direct group changes.

.. _ucs-operation-groups-management-cache:

Local group cache
=================

.. TODO: Rework this section

The user and computer information retrieved from the LDAP is cached by
the Name Server Cache Daemon (NSCD), see :ref:`computers-nscd`.

Since UCS 3.1, the groups are no longer cached via the NSCD for
performance and stability reasons; instead they are now cached by the
NSS module :program:`libnss-extrausers`. The group
information is automatically exported to the
:file:`/var/lib/extrausers/group` file by the
:file:`/usr/lib/univention-pam/ldap-group-to-file.py`
script and read from there by the NSS module.

In the basic setting, the export is performed once a day by a cron job
and is additionally started if the *Univention Directory Listener* has been inactive for 15
seconds. The interval for the cron update is configured in Cron syntax
(see :ref:`cron-local`) by the UCR variable
:envvar:`nss/group/cachefile/invalidate_interval`. This listener
module can be activated/deactivated via the UCR variable
:envvar:`nss/group/cachefile/invalidate_on_changes`
(``true``/``false``).

When the group cache file is being generated, the script can verify
whether the group members are still present in the LDAP directory. If
not only UMC modules are used for user management, this additional check
can be can be enabled by setting the UCR variable
:envvar:`nss/group/cachefile/check_member` to
``true``.

.. _ucs-operation-groups-management-ad-groups:

Synchronization of Active Directory groups when using Samba/AD
==============================================================

.. TODO: Rework through this section

If Samba/AD is used, the group memberships are synchronized between the
Samba/AD directory service and the OpenLDAP directory service by the
Univention S4 connector, i.e., each group on the UCS side is associated
with a group in Active Directory. General information on the Univention
S4 connector can be found in :ref:`windows-s4-connector`.

Some exceptions are formed by the *pseudo groups*,
sometimes also called system groups. These are only managed internally
by Active Directory/Samba, e.g., the ``Authenticated Users`` group includes a list
of all the users currently logged on to the system. Pseudo groups are
stored in the UCS directory service, but they are not synchronized by
the Univention S4 connector and should usually not be edited. This
applies to the following groups:

* ``Anonymous Logon``
* ``Authenticated Users``
* ``Batch``
* ``Creator Group``
* ``Creator Owner``
* ``Dialup``
* ``Digest Authentication``
* ``Enterprise Domain Controllers``
* ``Everyone``
* ``IUSR``
* ``Interactive``
* ``Local Service``
* ``NTLM Authentication``
* ``Network Service``
* ``Network``
* ``Nobody``
* ``Null Authority``
* ``Other Organization``
* ``Owner Rights``
* ``Proxy``
* ``Remote Interactive Logon``
* ``Restricted``
* ``SChannel Authentication``
* ``Self``
* ``Service``
* ``System``
* ``Terminal Server User``
* ``This Organization``
* ``World Authority``

In Active Directory/Samba, a distinction is made between the following
four AD group types. These group types can be applied to two types of
groups; *security groups* configure permissions
(corresponding to the UCS groups), whilst *distribution
groups* are used for mailing lists:

Local
   *Local* groups only exist locally on a host. A local group created in
   Samba/AD is synchronized by the Univention S4 Connector and thus also appears
   in the UMC module :guilabel:`Groups`. There is no need to create local groups
   in the UMC module.

Global
   *Global* groups are the standard type for newly created groups in the UMC
   module :guilabel:`Groups`. A global group applies for one domain, but it can
   also accept members from other domains. If there is a trust relationship with
   a domain, the groups there are displayed and permissions can be assigned.
   However, the current version of UCS does not support multiple domains/forests
   or outgoing trust relationships.

Domain local
   *Domain local* groups can also adopt members of other domains (insofar as
   there is a trust relationship in place or they form part of a forest). Local
   domain groups are only shown in their own domain though. However, the current
   version of UCS does not support multiple domains/forests or outgoing trust
   relationships.

Universal
   *Universal* groups can adopt members from all domains and these members are
   also shown in all the domains of a forest. These groups are stored in a
   separate segment of the directory service, the so-called *global catalog*.
   Domain forests are currently not supported by Samba/AD.

.. _ucs-operation-groups-management-memberof:

Overlay module for displaying the group information on user objects
===================================================================

Nubus only saves group membership properties in the group objects
and not in the respective user objects in the directory service.
However, some applications expect group membership properties at the user objects
in the attribute ``memberOf``.
An overlay module in the LDAP server makes it possible
to present these attributes automatically based on the group information.
Nubus doesn't write the additional attributes to the directory service.
The directory service shows the attributes on-the-fly through the overlay module
when it answers a query for a user object.

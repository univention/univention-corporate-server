.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _ucs-operation-groups:

****************
Group management
****************

This page describes how to manage groups in Nubus for UCS.
It covers UCS-specific aspects of group creation, nested groups, group caching,
synchronization of groups with Active Directory, and the group overlay module.
For general information about group management in Nubus,
see :external+uv-nubus-manual:ref:`nubus-groups` in :cite:t:`uv-nubus-manual`.

In addition to global groups in a Nubus domain,
there are also local user groups on each system,
which you predominantly use for hardware access.
You don't manage local groups through the *Management UI*,
but through the :file:`/etc/group` file.

.. _ucs-operation-groups-creation-assignment:

Group creation and assignment
=============================

To create groups in Nubus for UCS,
follow along the section
:external+uv-nubus-manual:ref:`nubus-groups`
in :cite:t:`uv-nubus-manual`.
It describes how to assign users to groups.
For a complete reference of the *Groups* management module,
see :external+uv-nubus-manual:ref:`nubus-groups-management`.

The following sections supplement that reference with specifics
that apply to Nubus for UCS.

.. _ucs-operation-groups-management-tab-general-name:

:menuselection:`General tab --> Name`
   For the reference,
   see :external+uv-nubus-manual:ref:`nubus-groups-management-tab-general-name`
   in :cite:t:`uv-nubus-manual`.

   By default, it isn't possible to create a group
   with the same name as an existing user.
   If the UCR variable
   :envvar:`directory/manager/user_group/uniqueness` has the value ``false``,
   Nubus doesn't run this check.

.. _ucs-operation-groups-management-tab-advanced-field-group-type:

:menuselection:`Advanced settings tab --> Windows --> group type`
   For the reference,
   see :external+uv-nubus-manual:ref:`nubus-groups-management-tab-advanced-field-group-type`
   in :cite:t:`uv-nubus-manual`.

   .. _ucs-operation-groups-management-tab-advanced-field-group-type-local:

   Local groups
      If you create a local group on a Windows server,
      only that server recognizes this group.
      A local group isn't available across the domain.
      In contrast, Nubus for UCS doesn't differentiate between local and global groups.
      After taking over an Active Directory domain,
      Nubus for UCS handles local groups in the same way as *Domain Groups*.

.. _ucs-operation-groups-management-nested:

Nested groups
=============

For a description of nested groups in Nubus,
see :external+uv-nubus-manual:ref:`nubus-groups-management-nested`
in :cite:t:`uv-nubus-manual`.
Additionally, the following applies to nested groups in Nubus for UCS.

Nubus runs a plausibility check
to detect cyclic dependencies in nested groups.
To deactivate this check, set the UCR variable
:envvar:`directory/manager/web/modules/groups/group/checks/circular_dependency`
to the value ``no``.
The default value is ``yes``.
If you modify groups without using the *Management UI*,
you must manually ensure that there are no cyclic memberships.

.. _ucs-operation-groups-management-cache:

Group caching
=============

Nubus uses the NSS module :program:`libnss-extrausers` for group caching.
The :file:`/usr/lib/univention-pam/ldap-group-to-file.py` script exports group information automatically
and writes it to the :file:`/var/lib/extrausers/group` file.
The NSS module then reads the group information from there.

By default, a cron job runs the export once a day.
Additionally, the :program:`ldap-group-to-file.py` export also runs
after the *Univention Directory Listener* has been inactive for 15 seconds.
You can configure the interval for the cron-based cache updates
in cron syntax using the
:envvar:`nss/group/cachefile/invalidate_interval`
UCR variable.
For the cron syntax, see :external+uv-ucs-manual:ref:`cron-local`
in :cite:t:`ucs-manual`.
You can activate or deactivate the update of the group cache file
through the *Univention Directory Listener* with the
:envvar:`nss/group/cachefile/invalidate_on_changes`
UCR variable.

.. TODO: Update link for the UCS Manual when information about cron syntax is available here.

When the :program:`ldap-group-to-file.py` script generates the group cache file,
it can verify
whether the group members still exist in the LDAP directory service.
If you use user management methods beyond the *Users* and *Groups* management module,
you can enable this additional verification
by setting the
:envvar:`nss/group/cachefile/check_member`
UCR variable to the value ``true``.

.. _ucs-operation-groups-management-ad-group-sync:

Active Directory group synchronization
======================================

If you have Samba installed in your domain of Nubus for UCS,
Nubus synchronizes the group memberships
between the Samba directory service and the OpenLDAP directory service
through the Univention :program:`S4 Connector`.
The connector associates each user group in Nubus for UCS
with a user group in Active Directory.
For information about the :program:`S4 Connector`,
see :external+uv-ucs-manual:ref:`windows-s4-connector`
in :cite:t:`ucs-manual`.

.. TODO: Replace the S4 Connector reference with a reference not directing to the UCS Manual.

.. note::

   Samba provides Active Directory compatible functionality.
   It operates a dedicated LDAP directory service.
   The :program:`S4 Connector` synchronizes the LDAP directory service in Samba
   with the OpenLDAP directory service in Nubus for UCS.

*Pseudo groups*, also called system groups,
are exceptions to this synchronization.
Only Active Directory and Samba manage such *pseudo groups* internally.
For example, the ``Authenticated Users`` user group
includes a list of users currently signed in to the domain.
Nubus stores *pseudo groups* in its directory service,
but the :program:`S4 Connector` doesn't synchronize them.
Don't edit these groups.
The behavior applies to the following *pseudo groups*:

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

Active Directory and Samba distinguish between the following group types.
The :program:`S4 Connector` synchronizes these groups.
In the LDAP directory service, the groups have attributes to label the group types.
However, the group types only have a meaning in Active Directory.
Nubus doesn't evaluate the group types.

Local
   *Local* groups exist only on a single host.
   The :program:`S4 Connector` synchronizes local groups created in Samba.
   Therefore, they also appear in the *Groups* management module in the *Management UI*.
   There is no need to create local groups in the *Groups* management module.

Global
   *Global* groups are the default type
   when you create groups in the *Groups* management module.
   A global group applies to one domain
   but can accept members from other domains.
   If there is a trust relationship with a domain,
   the *Groups* management module shows the groups from other trusted domains
   and you can assign permissions to them.

   .. important::

      Nubus for UCS doesn't support multiple domains or forests or outgoing trust relationships.

Domain local
   *Domain local* groups can also include members from other domains
   if there's a trust relationship or if they're part of a forest.
   The *Groups* management module shows the domain local groups only in their own domain.

   .. important::

      Nubus for UCS doesn't support multiple domains or forests or outgoing trust relationships.

Universal
   *Universal* groups can adopt members from all domains
   and these members are visible across all domains in a forest.
   The *global catalog* is a separate segment of the Samba directory service
   and it stores universal groups.
   The :program:`S4 Connector` doesn't synchronize the *global catalog* to OpenLDAP.

   The Active Directory capability in Samba doesn't support domain forests.

You can apply the group types to the following kind of groups:

Security groups
   Administrators use them to assign permissions,
   similar to user groups in Nubus.

Distribution groups
   Active Directory uses them for mailing lists.

.. _ucs-operation-groups-management-overlay:

Group overlay module
====================

Nubus only saves group membership properties in the group objects
and not in the respective user objects in the directory service.
However, some applications expect group membership properties at the user objects
in the attribute ``memberOf``.
An overlay module in the OpenLDAP directory server in Nubus allows presenting
these attributes automatically based on the group information.
Nubus doesn't write the additional attributes to the directory service.
The directory service shows the attributes on-the-fly through the overlay module
when it answers a query for a user object.

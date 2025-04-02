.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-intro:

#####################################################################
Univention Corporate Server - Delegative administration documentation
#####################################################################

.. warning::

   Delegative administration is an experimental feature.
   Don't use it in production yet.
   There are still many shortcomings
   and in particular things like configuration can and will change in the future.

This document describes the concepts, setup, and configuration
of delegative administration for Univention Nubus
and wants to enable experienced Nubus administrators
to test this experimental feature.

With delegative administration Univention Nubus provides a mechanism
that enables organizations to implement a decentralized model of managing the LDAP directory through UMC.

It's possible to assign roles to user objects.
The roles define what an user object can do to the LDAP directory,
which objects the user can read, modify, create, or delete.

A common use case is a manager or administrator for an organizational unit within the directory.
Users with such an assigned role are able to manage other user objects and group objects of a specific position in the directory,
such as ``ou=bremen,dc=ldap,dc=base``.
However, depending on the exact configuration,
users with such a role can't manage or even see objects from other positions.

The Univention development team is happy to receive feedback
to improve the experimental version of delegative administration
and to make it a useful and supported addition to the Nubus product.
For general feedback, use the `feedback form <https://www.univention.com/feedback/?ext-delegative-administration=generic>`_.

.. _da-technical-requirements:

**********************
Technical requirements
**********************

The current implementation has the following technical requirements:

* You need a UCS system with version 5.2-1 and the latest errata updates.
* Delegative administration only supports the UCS system roles |UCSPRIMARYDN| and |UCSBACKUPDN|.

.. _da-limits:

***********************
Limits and known issues
***********************

As already said,
delegative administration is in an early development stages
and many things are still missing or not fully implemented.
Beware the following limitations:

* This is a minimal viable product without an update path, just for testing.
  Don't use it in production, yet.

* Use it only in UCS environments with up to 2,000 directory objects.

* The configuration and customization may break any time.

* Delegative administration is only available for the UDM modules in UMC.
  In particularly, this has no effect
  on what modules users can see and use in UMC,
  just what they can do with these modules.
  You have to separately configure
  which user can see and use which UMC module.

  .. FIXME: This item has a mixture of UDM modules, UMC modules, and UDM modules in the UDM module for UMC. It's confusing. We need to be more specific here.

  .. TODO: Refer to reader to content about how they configure which user sees which UMC module. Otherwise, we leave them alone here.

.. _da-features:

********
Features
********

* Administrators can define roles
  and added to user objects and group objects to them.
  Group members inherit the roles from the group object.
  Therefore, you can implement authorization based on group membership.

  .. FIXME: Is it really about authorization?

* Every role defines a list of permissions.
  Permissions define what a role can do in the directory.

* The backend of the UMC UDM modules checks the authorization for the roles of the signed-in user
  before accessing the directory database
  or returning directory objects from the database.

* Delegative administration provides the following default roles:

  ``domainadmins``
    Can manage every object.

  ``ouadmins``
    Can manage a particular position in the directory.

.. _da-setup-test-env:

****************************
Setup of an test environment
****************************

Univention released the preview for the delegative administration as a normal errata update for UCS 5.2-1.
However, you as an administrator need to explicitly activate the feature
and perform some additional steps to test its functionality.

.. _da-setup-test-env-preparation:

Preparation
===========

To prepare a UCS 5.2-1 test environment for using delegative administration,
use the following steps:

#. Set up a new UCS 5.2-1 |UCSPRIMARYDN| test system
   and upgrade to the latest errata updates.

#. Add the role ``umc:udm:domainadmin`` as ``guardianMemberRoles`` to the group ``Domain Admins``.
   ``umc:udm:domainadmin`` is a default role to allow access to the directory for ``Administrators``.
   Use the command in :numref:`da-setup-test-env-preparation-add-role-listing`.

   .. code-block:: console
      :caption: Add ``umc:udm:domainadmin`` as default role for domain administrators
      :name: da-setup-test-env-preparation-add-role-listing

      $ udm groups/group modify \
         --dn "cn=Domain Admins,cn=groups,$(ucr get ldap/base)" \
         --append guardianMemberRoles="umc:udm:domainadmin"

#. By default,
   only members of the user group ``Domain Admins`` can see and use the user and group modules in UMC.

   .. TODO: Remove, because it's duplicate content from the limitiation:

      Delegative administration is currently only implemented for what can be done with these modules, not which modules a user can see in UMC.

   To properly test the delegative administration feature,
   you need to assign the right
   to see and use the users and group module in UMC
   to every user object.
   Run the command in :numref:`da-setup-test-env-preparation-assign-rights-listing`.

   .. code-block:: console
      :caption: Assign the right to see the users and group modules in UMC to every user object
      :name: da-setup-test-env-preparation-assign-rights-listing

      $ udm policies/umc modify \
          --dn "cn=default-umc-users,cn=UMC,cn=policies,$(ucr get ldap/base)" \
          --append allow="cn=udm-groups,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)" \
          --append allow="cn=udm-users,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)" \
          --append allow="cn=udm-syntax,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)"

.. _da-setup-test-env-activate:

Activate delegative administration
==================================

To activate delegative administration on every UCS system in your test environment,
you need to run the commands in :numref:`da-setup-test-env-activate-listing`
on every system.

.. code-block:: console
   :caption: Activate delegative administration on a UCS system
   :name: da-setup-test-env-activate-listing

   $ ucr set umc/udm/delegation='true'
   $ service univention-management-console-server restart

.. _da-setup-test-env-test:

Test delegative administration
==============================

To test delegative administration, use the following steps:

#. Sign in as ``Administrator`` to the UMC.

   You notice no difference.
   You can still see all user objects or group objects
   and are able to create and modify every object.

#. Create a new test user account without a role.
   Use the command in :numref:`da-setup-test-env-test-listing`.

   .. code-block:: console
      :caption: Create user object without a role
      :name: da-setup-test-env-test-listing

      $ udm users/user create \
         --position="cn=users,$(ucr get ldap/base)" \
         --set username=test1 \
         --set password=univention \
         --set lastname=test

#. To test with the created user object, open a private browser window or sign out.

#. Sign in to the UMC as ``test1`` and open the users module.
   The result list is empty,
   because the user object ``test1`` has no permission to read objects from the LDAP directory.

.. _da-setup-test-env-ouadmin:

Preparation for testing the ``ouadmin`` default role
====================================================

A more interesting example is the role ``ouadmin``.
This role gives the user the ability to manage a position of the directory.
User objects with this role have the following permissions:

* They can see, create, modify, and delete user objects in their organizational unit.

* They can't see or modify user objects or group objects in any other position.

* They can't modify the attribute ``guardianRoles`` of users.
  This role can't manage roles.

* They can see user group objects in the container :samp:`cn=groups,{LDAP_BASE}`.

To test this role, you need to prepare your test environment.
The following script creates and configures 10 organizational units,
one user object with the role ``ouadmin`` for each organizational unit
and 10 user objects within each organizational unit.
Run the commands in :numref:`da-setup-test-env-ouadmin-listing`.

.. code-block:: console
   :caption: Create 10 organizational units with 10 user objects each
   :name: da-setup-test-env-ouadmin-listing

   for i in $(seq 1 10); do
     # create some structure and a ouadmin user
     ou="ou${i}"
     udm container/ou create \
       --set name="$ou" \
       --set groupPath=1 \
       --set userPath=1
     udm container/cn create \
       --position="ou=$ou,$(ucr get ldap/base)" \
       --set name=users \
       --set userPath=1
     udm container/cn create \
       --position="ou=$ou,$(ucr get ldap/base)" \
       --set name=groups \
       --set groupPath=1
     udm users/user create \
       --position="cn=users,$(ucr get ldap/base)" \
       --set username="${ou}-admin" \
       --set password=univention \
       --set lastname="${ou}-admin" \
       --append guardianRoles="umc:udm:ouadmin&umc:udm:ou=${ou}"
     # create some users
     for j in $(seq 1 10); do
       username="user${j}-${ou}"
       udm users/user create \
         --position="cn=users,ou=${ou},$(ucr get ldap/base)" \
         --set username="$username" \
         --set password=univention \
         --set lastname="$username"
     done
   done

Now you can sign in to UMC with the user ``ou1-admin``, the password ``univention``,
and open the users module.
You see only the users of the organizational unit ``ou1``, nothing else.

You can also manually add the role ``umc:udm:ouadmin&umc:udm:ou=ou2`` to the ``guardianRoles`` property of the user ``ou1-admin``.
The user then has ``ouadmin`` rights for two the organizational units ``ou=ou1`` and ``ou=ou2``.

.. _da-setup-test-env-deactivate:

Deactivate delegative administration
====================================

To deactivate delegative administration,
you need to run the commands in :numref:`da-setup-test-env-deactivate-listing`
on every UCS system in your test environment.

.. code-block:: console
   :caption: Deactivate delegative administration on one UCS system
   :name: da-setup-test-env-deactivate-listing

   $ ucr unset umc/udm/delegation
   $ service univention-management-console-server restart

.. _da-concepts:

********
Concepts
********

This section describes the roles, capabilities, and permissions
and what an actor can do to a target object.
For more background information about concepts and ideas behind this concept,
refer to :cite:t:`guardian-doc`.

Actor
  Is the person or entity that wants to perform an operation.

Target object
  Is the object in the LDAP directory on which delegative administration performs the operation.

Permissions
  Permissions define what the actor can do to an UDM object.
  Which properties the actor can seen or modify
  and if the actor can create or remove objects.

Capabilities
  A capability is a condition and a list of permissions
  that apply if the condition is true.
  The only condition in the current implementation is a position in the LDAP directory.
  The condition applies if the position of the target object and the position of capability match.
  In this case all the permissions of the capability apply for the actor.

Roles
  A role is basically a container for a list of capabilities.
  Roles have a name
  that must consist only of letters and numbers.
  Every role has a configuration in a JSON format data structure.

  Administrators can assign roles to user objects as ``guardianRoles``,
  or to group objects as ``guardianMemberRoles``.
  In case of an assignment to a group object,
  all members of a group inherit the role of the group.

  When setting the roles on user or group objects,
  you need to add the prefix ``umc:udm:`` to the role.
  Adding the role ``domainadmin`` to a user object on the command line looks like :numref:`da-concepts-listing`.

  .. code-block:: console
     :caption: Add role ``domainadmin`` to a user object
     :name: da-concepts-listing

     $ udm users/user modify --dn … --append guardianRoles="umc:udm:domainadmin"

.. _da-concepts-context:

Role context
============

Roles can have an optional context.
This context is an LDAP DN, without the LDAP base.
It defines the position in the LDAP directory for which this role applies.

One example is the role ``ouadmins``.
This role has one definition for what it can do.
However, you may want to differentiate between different ``ouadmins`` for different organizational units.

You can differentiate by setting a context when you assign the role to a user object as shown in
:numref:`da-concepts-context-listing`.

.. code-block::
   :caption: Schema for setting a context when assigning the role
   :name: da-concepts-context-listing

   user1 -> guardianRoles -> umc:udm:ouadmin&um:udm:ou=bremen
   user2 -> guardianRoles -> umc:udm:ouadmin&um:udm:ou=berlin

``umc:udm:``
   is a prefix, that we have to set before the role and the context.

``ouadmin``
   is the role.

``&``
   is the separator between the role and the context.

``ou=bremen``
   is a position in the LDAP directory in form of an LDAP DN,
   without the LDAP base, for which the role applies.

The ``user1`` and ``user2`` user objects have the same permissions.
The permissions derive from the role ``ouadmin``.
And the different positions in the LDAP directory derive from the context.

.. warning::

   Not every role evaluates the context.
   Whether a context is meaningful for a role depends on the configuration of the role.
   For example the role ``domainadmin`` doesn't evaluate the context,
   wherefore a context for this role has no effect.
   On the other hand ``ouadmin`` without a context is basically useless.

.. _da-concepts-example:

Configuration of roles
======================

Bringing all this together,
a generic form of this configuration looks like the example in :numref:`da-concepts-example-listing`.

.. code-block:: json
   :caption: Example for role configuration
   :name: da-concepts-example-listing

   {
     "ROLE_NAME": [
       {
         "condition": {
           "position": "LDAP_DN | $CONTEXT | *",
           "scope": "subtree | base",
         },
         "permissions": {
           "UDM_MODULE_NAME | *": {
             "attributes": {
               "ATTRIBUTE_NAME | *": "read | write | none"
             },
             "create": "true | false",
             "delete": "true | false"
           }
         },
         "permission": {
            "..."
         }
       },
       {
           "condition": "..."
       }
     ],
     "ROLE_NAME": "..."
   }

``ROLE_NAME``
   name of the role.
   Can be any string.

``condition → position``
   the condition position of the capability.
   It can have one of the following values:

   ``LDAP_DN``
     any position of your LDAP directory in form of a DN, without the LDAP base

   ``$CONTEXT``
     a placeholder.
     UCS replaces this keyword with the context of a role.

   ``*``
     wildcard to match anything.

``condition → scope``
   the scope of this capability.
   It can have one of the following values:

   ``subtree``
     permissions apply for this position and everything below this position.

   ``base``
     permissions apply for this position only.

``permissions → UDM_MODULE_NAME``
   permissions for UDM object.
   It can have one of the following values:

   * The name of a UDM object, like ``users/user``.

   * The wildcard ``*``, which matches every UDM object.

``permissions → UDM_MODULE_NAME → attributes → ATTRIBUTE_NAME``
   permissions for properties of a UDM object.
   It can have one of the following values:

   * The name of a UDM object property, like ``username``.

   * The wildcard ``*``, which matches every property.

   * As value you can set one of the following:

     * ``none`` for not readable.

     * ``read`` for not writable.

     * ``write`` for writable.

``permissions → UDM_MODULE_NAME → create``
   defines whether users can create objects.
   It can have either the value ``true`` or ``false``.

``permissions → UDM_MODULE_NAME → delete``
   defines whether users can remove objects.
   It can have either the value ``true`` or ``false``.

The default role ``domainadmin`` has configuration in :numref:`da-concepts-example-domainadmin-listing`.

.. code-block:: json
   :caption: Default configuration for ``domainadmin`` role
   :name: da-concepts-example-domainadmin-listing

     "domainadmin": [
       {
         "condition": {
           "position": "*"
         },
         "permissions": {
           "*": {
             "attributes": {
               "*": "write"
             },
             "create": true,
             "delete": true
           }
         }
       }
     ]

The ``domainadmin`` role has one capability,

* that matches for all positions of target objects
* and gives write permissions to all UDM properties of all UDM objects
* and permission to create and remove every UDM object.

.. _da-concepts-priorities:

Priorities
==========

The more specific position condition or permission configuration has higher
priority.

``Position condition``
  Every capability binds to a position.
  In this position, you can use a LDAP DN,
  the keyword ``$CONTEXT`` and a wildcard ``*``.
  If a role has multiple capabilities,
  the match of a capability position with the target object position
  by the most specific LDAP DN has the highest priority.
  Then ``$CONTEXT`` and the wildcard ``*`` have the lowest priority.

``UDM modules in permissions``
  In permissions you can define UDM module names or a wildcard ``*``.
  If there is a permission for the UDM module of the target object
  UCS uses it, otherwise the ``*`` permission.

``Properties in permissions``
  Definitions of real property names have higher priority
  than the wildcard ``*``.

``Roles``
  It's currently undefined if an actor has multiple roles
  and these roles have capabilities with the same position condition.
  One of these capabilities matches, but it's undefined which one.

.. _da-concepts-custom-roles:

Custom roles
============

You can define your own roles in a JSON format data structure in the file
:file:`/etc/umc-udm-roles.json`
as shown in :numref:`da-concepts-custom-roles-listing`.

.. code-block:: json
   :caption: Define custom roles in JSON format data structure
   :name: da-concepts-custom-roles-listing

   {
     "myadmin": [
       "condition": {
         "position": "..."
       }
       "permissions": {
         "users/user": {
           "attributes": {
              "username": "write",
              "*": "read"
           }
         }
       }
     ]
   }

You can set the role ``umc:udm:myadmin`` to user or group objects.

.. _da-troubleshooting:

***************
Troubleshooting
***************

When you encounter problems or errors,
consule the following files:

:file:`/var/log/univention/management-console-server.log`
   Contains log information for the UMC server.

:file:`/var/log/univention/management-console-module-udm.log`
   Contains log information for the UDM UMC module.

You may also want to increase the log level for the UMC server and module process
as shown in :numref:`da-troubleshooting-log-level-listing`.

.. code-block:: console
   :caption: Increase log levels
   :name: da-troubleshooting-log-level-listing

   $ ucr set umc/server/debug/level='4'
   $ ucr set umc/module/debug/level='4'
   $ service univention-management-console-server restart

.. _da-config-reference:

************************************
Description of configuration options
************************************

The following files in JSON format define the default roles and custom roles:

:file:`/usr/share/univention-directory-manager-modules/umc-udm-roles.json`
   Contains the default roles ``domainadmin`` and ``ouadmin``:

   .. important::

      Don't change this file.
      UCS updates overwrite it.

:file:`/etc/umc-udm-roles.json`
   Can contain custom role definitions.

   This file doesn't exist by default.
   However, you can create this file
   and add custom role definitions.
   The structure of the file may change at any time.
   If you have multiple servers in your test environment,
   you have to manually keep this file in synchronization between servers.

The following references show the available settings for delegative administration:

.. envvar:: umc/udm/delegation

   Activate or deactivate delegative administration for UMC and UDM.

   Possible values:
      ``true`` or ``false``.

.. only:: html or linkcheck or spelling

   ************
   Bibliography
   ************

.. bibliography::

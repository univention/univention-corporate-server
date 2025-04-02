.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-intro:

#####################################################################
Univention Corporate Server - Delegative administration documentation
#####################################################################

.. warning::

   This is an experimental feature not meant to be used in production
   environments. There are still many shortcomings and in particular things
   like configuration can and will change in the future.

This article describes the concepts, setup and configuration of delegative
administration for Univention Nubus and wants to enable experienced Nubus
administrators to test this new, experimental feature.

With delegative administration we want to provide a mechanism whereby
organizations are enabled to implement a decentralized model of managing the
LDAP directory via UMC.

It will be possible to assign roles to user objects. These roles define what
an user object can do to the LDAP directory, which objects the user can
read, modify, create or delete.

A common use case is a manager or administrator for an organizational unit
within the directory. User objects with such a role will be able to manage
other user and group objects of a specific position of the directory like
``ou=bremen,dc=ldap,dc=base``. But, depending on the exact configuration, will
not be able to manage or even see objects from other positions.

We will be happy to receive feedback to improve this first experimental
version of delegative administration and to make it a useful and
supported addition to the Nubus product in the future.

.. _da-technical-requirements:

**********************
Technical requirements
**********************

The current implementation has some technical requirements:

* You need a UCS server with version 5.2-1 and the latest errata updates.
* Only the roles |UCSPRIMARYDN| and |UCSBACKUPDN| are supported.

.. _da-limits:

***********************
Limits and known issues
***********************

As said before, this is in the early stages of its implementation and many
things are still missing or not fully implemented:

* This is a Minimum Viable Product without an update path, just for testing.
* Only for environments with up to 2.000 objects.
* The configuration and customization may break any time.
* Delegative administration is currently only available for the UDM modules in
  UMC. In particularly this has currently no effect on what modules users can see
  and use in UMC, just what they can do with these modules.
  You have to separately configure which user is allowed to see and use which
  UMC module.

.. _da-features:

********
Features
********

* Roles can be defined and added to user and group objects. Group members will
  inherit the roles from the group. So you will still be able to implement
  authorization based on group membership.
* Every role defines a list of permissions and these permissions define
  what this role can do in the directory.
* The back-end of the UMC UDM modules checks the authorization for the roles
  of the logged in user before accessing the LDAP database or returning
  objects from the database.
* There are two default roles, ``domainadmins`` - can manage every object -
  and ``ouadmins`` - can manage a particular position in the directory.

.. _da-setup-test-env:

****************************
Setup of an test environment
****************************

This preview is released as a normal errata update for UCS 5.2-1.
But you have to activate this feature and perform some additional steps to be able to test the new functionality.

.. _da-setup-test-env-preparation:

Preparation
===========

* Set up a new UCS 5.2-1 |UCSPRIMARYDN| test system and install the latest
  errata updates.

* Add the role ``umc:udm:domainadmin`` as ``guardianMemberRoles`` to the group
  ``Domain Admins`` - this is a default role to allow access to the directory for
  ``Administrators``, just like without this feature:

  .. code-block:: console

     $ udm groups/group modify \
       --dn "cn=Domain Admins,cn=groups,$(ucr get ldap/base)" \
       --append guardianMemberRoles="umc:udm:domainadmin"

* By default only members of the group ``Domain Admins`` can see and use the
  user and group modules in UMC. Delegative administration is currently only
  implemented for what can be done with these modules, not which modules a
  user can see in UMC.
  In order to properly test the new feature, we just give every user the right
  to see and use the users and group module in UMC:

  .. code-block:: console

    $ udm policies/umc modify \
      --dn "cn=default-umc-users,cn=UMC,cn=policies,$(ucr get ldap/base)" \
      --append allow="cn=udm-groups,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)" \
      --append allow="cn=udm-users,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)" \
      --append allow="cn=udm-syntax,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)"

.. _da-setup-test-env-activate:

Activate delegative administration
==================================

You can activate delegative administration with the following commands on every
UCS server in your test environment:

.. code-block:: console

   $ ucr set umc/udm/delegation='true'
   $ service univention-management-console-server restart

.. _da-setup-test-env-test:

Test delegative administration
==============================

Now log in as ``Administrator`` to the UMC. You should notice no difference.
You can still see all user or group objects and should be able to create and
modify every objects.

Create a new test user account without a role:

.. code-block:: console

   $ udm users/user create \
     --position="cn=users,$(ucr get ldap/base)" \
     --set username=test1 \
     --set password=univention \
     --set lastname=test

Login to the UMC as ``test1`` and open the users module. The result list
should be empty as this user does not have any permissions to read objects from
the LDAP directory.

.. _da-setup-test-env-ouadmin:

Preparation for testing the ``ouadmin`` default role
====================================================

A more interesting example is the role ``ouadmin``. This role gives the user
the ability to manage a position of the directory. User objects with this role
can:

* Can see, create, modify and delete user objects in "their" organizational unit.
* Can not see or modify user or group objects in any other position.
* Can not modify the attribute ``guardianRoles`` of users, this role can not manage
  roles.
* Can see group objects in the container ``cn=groups,LDAP_BASE``.

In order to test this role, we have to prepare our test environment.
The following script will create and configure 10 organizational units, an user
object with the role ``ouadmin`` for each organizational unit and 10 user
objects within each organizational unit:

.. code-block:: bash

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

Now you can login to UMC with the user ``ou1-admin``, password ``univention``,
and open the users module. You should see only the users of the organizational
unit ``ou1``, nothing else.

You can also manually add the role ``umc:udm:ouadmin&umc:udm:ou=ou2`` to the
``guardianRoles`` property of the user ``ou1-admin``. The user will now have
``ouadmin`` rights for two organizational units - ``ou=ou1`` and ``ou=ou2``.

.. _da-setup-test-env-deactivate:

Deactivate delegative administration
====================================

You can deactivate delegative administration with the following commands on every
UCS server in your test environment:

.. code-block:: console

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

``Actor``
  Is the person or entity that wants to perform an operation.

``Target object``
  Is the object in the LDAP directory on which the operation is performed.

``Permissions``
  Permissions define what the actor can do to an UDM object. Which properties
  the actor can seen or modify and if the actor can create or remove objects.

``Capabilities``
  A capability is a condition and a list of permissions that apply if the
  condition is met. The only condition in the current implementation is
  a position in the LDAP directory. The condition is met if the position of
  the target object and the position of capability match. In this case all
  the permissions of the capability apply for the actor.

``Roles``
  A role is basically a container for a list of capabilities. Roles have a name
  that must consist only of letters and numbers. Every role has a
  configuration in the form of a ``json`` data structure.

  Roles can be assigned to user objects as ``guardianRoles`` or to group
  objects as ``guardianMemberRoles``, in this case all members of a group will
  inherit the role of the group.

  When setting the roles on user or group objects, you need to add the
  prefix ``umc:udm:`` to the role. Adding the role ``domainadmin`` to a
  user object on the command line looks like this:

  .. code-block:: console

     $ udm users/user modify --dn ... --append guardianRoles="umc:udm:domainadmin"

.. _da-concepts-context:

Role context
============

Roles can have an optional context. This context is an LDAP DN, without the
LDAP base, and defines the position in the LDAP directory for which this role applies.

And example is the role ``ouadmins``. We have one definition for
what this role can do, but we may need to differentiate between different
``ouadmins`` for different organizational units.

This can be achieved by setting a context when assigning the role to a user
object:

.. code-block::

   user1 -> guardianRoles -> umc:udm:ouadmin&um:udm:ou=bremen
   user2 -> guardianRoles -> umc:udm:ouadmin&um:udm:ou=berlin

* ``umc:udm:`` is a prefix, that we have to set before the role and the
  context
* ``ouadmin`` is the role
* ``&`` is the separator between the role and the context
* ``ou=bremen`` is a position in the LDAP directory in form of an LDAP DN,
  without the LDAP base, for which the role applies

``user1`` and ``user2`` have the same permissions - derived from the role
``ouadmin`` - but for different positions in the LDAP directory - derived from the
context.

.. warning::

   Not every role evaluates the context. Whether or not a context is
   meaningful for a role depends on the configuration of the role. For example
   the role ``domainadmin`` does not evaluate the context, a context for this
   role has no effect. On the other hand ``ouadmin`` without a context is
   basically useless.

.. _da-concepts-example:

Configuration of roles
======================

If we bring all this together, a generic form of this configuration looks like
this:

.. code-block:: json

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

* ``ROLE_NAME`` name of the role, can be any string

* ``condition -> position`` the condition position of the capability, can be

  * ``LDAP_DN`` any position of your LDAP directory in form of a DN, without the LDAP base

  * ``$CONTEXT`` this keyword will be replaced by the context of a role

  * ``*`` wildcard to match anything

* ``condition -> scope`` the scope of this capability, can be

  * ``subtree`` permissions apply for this position and everything below this
    position

  * ``base`` permissions apply for this position only

* ``permissions -> UDM_MODULE_NAME`` permissions for UDM object, can be

  * the name of an UDM object, like ``users/user``

  * or the wildcard ``*``, which matches every UDM object

* ``permissions -> UDM_MODULE_NAME -> attributes -> ATTRIBUTE_NAME`` permissions for properties of an
  UDM object, can be

  * the name of an UDM object property, like ``username``

  * or the wildcard ``*``, which matches every property

  * as value you can set

    * ``none`` for not readable

    * ``read`` for not writable

    * ``write`` for writable

* ``permissions -> UDM_MODULE_NAME -> create`` defines whether objects can be
  created, can be ``true`` or ``false``

* ``permissions -> UDM_MODULE_NAME -> delete`` defines whether objects can be
  removed, can be ``true`` or ``false``

For the default role ``domainadmin`` we have this configuration:

.. code-block:: json

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

This role has one capability

* that matches for all positions of target objects and
* gives write permissions to all UDM properties of all UDM objects and
* permission to create and remove every UDM object.

.. _da-concepts-priorities:

Priorities
==========

The more specific position condition or permission configuration has higher
priority.

``Position condition``
  Every capability is bound to a position. In this position a LDAP DN, the
  keyword ``$CONTEXT`` and a wildcard ``*`` can be used. If a role has
  multiple capabilities the match of a capability position with the target
  object position by the most specific LDAP DN has the highest priority.
  Then ``$CONTEXT`` and the wildcard ``*`` has the lowest priority.

``UDM modules in permissions``
  In permissions you can define UDM module names or a wildcard ``*``.
  If there is a permission for the UDM module of the target object
  it will be used, otherwise the ``*`` permission.

``Properties in permissions``
  Definitions of real property names have higher priority than the
  wildcard ``*``.

``Roles``
  It is currently undefined if an actor has multiple roles and these roles
  have capabilities with the same position condition. On of these capabilities
  will match, but it is undefined which.

.. _da-concepts-custom-roles:

Custom roles
============

You can define your own roles in a ``json`` data structure in the file
:file:`/etc/umc-udm-roles.json`.

.. code-block:: json

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

The following files can be consulted in case of problems or errors.

:file:`/var/log/univention/management-console-server.log`
   Contains log information for the UMC server.

:file:`/var/log/univention/management-console-module-udm.log`
   Contains log information for the UDM UMC module.

You may also want to increase the debug level for the UMC server and module
process.

.. code-block:: console

   $ ucr set umc/server/debug/level='4'
   $ ucr set umc/module/debug/level='4'
   $ service univention-management-console-server restart

.. _da-config-reference:

************************************
Description of configuration options
************************************

The following files in ``json`` format  define the default roles and custom roles:

:file:`/usr/share/univention-directory-manager-modules/umc-udm-roles.json`
   Contains the default roles ``domainadmin`` and ``ouadmin``:

   Please do not change this file. This file will be overwritten by updates.

:file:`/etc/umc-udm-roles.json`
   Can contain custom role definitions.

   This file does not exist by default. But you can create this file and add
   custom role definitions. The format of the file may change at any time.
   If you have multiple servers in your test environment you have to manually
   keep this file in sync between servers.

The following references show the available settings for delegative
administration.

.. envvar:: umc/udm/delegation

   Activate or deactivate delegative administration for UMC/UDM

   Possible values:
      ``true`` or ``false``

.. only:: html or linkcheck or spelling

   ************
   Bibliography
   ************

.. bibliography::

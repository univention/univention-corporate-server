.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-concepts:

********
Concepts
********

This section describes the roles, capabilities, and permissions
and what an actor can do to a target object.

.. glossary::

   Actor
     Is the person or entity that wants to perform an operation.

   Target object
     Is the object in the LDAP directory on which an actor performs the operation.

   Permissions
     Permissions define what the actor can do to an object.
     Which properties the actor can see or modify
     and if the actor can create or remove objects.

   Position condition
     Permissions apply if a position condition matches.
     The only condition in the current implementation is the position of the target object in the LDAP directory.
     The condition applies if the position of the target object matches the position of the condition.

   Capabilities
     A capability is a condition and a list of permissions that apply if the condition matches.
     In this case all the permissions of the capability apply for the actor.

   Roles
     A role is basically a container for a list of capabilities.
     Roles have a name
     that must consist only of letters and numbers.
     Every role has a configuration in a JSON format data structure.

     Administrators can assign roles to user objects as ``guardianRoles``,
     or to group objects as ``guardianMemberRoles``.
     In group objects with a role assignment,
     all group member objects inherit the role of the group.

     When you assign the roles to user objects or group objects,
     you need to add the prefix ``umc:udm:`` to the role.
     To add the role ``domainadmin`` to a user object,
     the command looks like :numref:`da-concepts-listing`.

     .. code-block:: console
        :caption: Add role ``domainadmin`` to a user object
        :name: da-concepts-listing

        $ udm users/user modify --dn "$LDAP_DN" --append guardianRoles="umc:udm:domainadmin"

.. seealso::

   :external+guardian-doc:ref:`guardian-terminology`
      in :cite:t:`guardian-doc`
      for more background information about concepts and ideas behind this concept.

.. _da-concepts-context:

Role context
============

Roles can have an optional context.
This context is an LDAP DN, without the LDAP base.
It defines the position in the LDAP directory for which this role applies.

One example is the role ``ouadmins``.
This role has one definition for what it can do.
However, you may want to differentiate between different ``ouadmins`` for different organizational units.

When you assign the role to the user object,
as shown in :numref:`da-concepts-context-listing`,
you can assign different contexts.

.. code-block::
   :caption: Schema for setting a context when assigning the role
   :name: da-concepts-context-listing

   user1 → guardianRoles → umc:udm:ouadmin&um:udm:ou=bremen
   user2 → guardianRoles → umc:udm:ouadmin&um:udm:ou=berlin

A role context definition has the following elements:

``umc:udm:``
   is a prefix
   that you need to put before the role and the context.

``ouadmin``
   is the role.

``&``
   is the separator between the role and the context.

``ou=bremen``
   is a position in the directory structure in form of an LDAP DN,
   without the LDAP base, for which the role applies.

The ``user1`` and ``user2`` user objects have the same permissions.
The permissions derive from the role ``ouadmin``.
And the different positions in the LDAP directory derive from the context.

.. important::

   Not every role evaluates the context.
   Whether a context is meaningful for a role depends on the configuration of the role.

   For example the role ``domainadmin`` doesn't evaluate the context,
   wherefore a context for this role has no effect.
   On the other hand ``ouadmin`` without a context is basically useless.

.. _da-concepts-example:

Configuration of roles
======================

Bringing all this together,
:numref:`da-concepts-example-listing`
shows an example for a generic form of this configuration in JSON format.

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

``condition.position``
   the condition position of the capability.
   It can have one of the following values:

   :``LDAP_DN``: Any position of your LDAP directory in form of a DN, without the LDAP base

   :``$CONTEXT``: A placeholder.
        UCS replaces this keyword with the context of a role.

   :``*``: Wildcard to match anything.

``condition.scope``
   the scope of this capability.
   It can have one of the following values:

   :``subtree``: Permissions apply for this position and everything below this position.

   :``base``: Permissions apply for this position only.

:samp:`permissions.{UDM_MODULE_NAME}`
   permissions for UDM object.
   It can have one of the following values:

   :``UDM_MODULE_NAME``: The name of a UDM object, like ``users/user``.
   :``*``: The wildcard ``*`` that matches every UDM object.

:samp:`permissions.{UDM_MODULE_NAME}.attributes.{ATTRIBUTE_NAME}`
   permissions for properties of a UDM object.
   It can have one of the following values:

   :``ATTRIBUTE_NAME``: The name of a UDM object property, like ``username``.
   :``*``: The wildcard ``*``, which matches every property.

   * As value you can set one of the following:

     :``none``: not readable.
     :``read``: not writable.
     :``write``: writable.

:samp:`permissions.{UDM_MODULE_NAME}.create`
   defines whether users can create objects.
   It can have either the value ``true`` or ``false``.

:samp:`permissions.{UDM_MODULE_NAME}.delete`
   defines whether users can remove objects.
   It can have either the value ``true`` or ``false``.

The default role ``domainadmin`` has the configuration in :numref:`da-concepts-example-domainadmin-listing`.
The configuration defines one capability,

* that matches for all positions of target objects
* and gives write permissions to all UDM properties of all UDM objects
* and permission to create and remove every UDM object.

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

.. _da-concepts-priorities:

Priorities
==========

The more specific a position condition or a permission configuration is,
the higher its priority.
The following priority rules exist in the delegative administration:

``Position condition``
  Every capability binds to a position.
  In this position, you can use an LDAP DN,
  the keyword ``$CONTEXT`` and a wildcard ``*``.
  If a role has multiple capabilities,
  the match of a capability position with the target object position
  by the most specific LDAP DN has the highest priority.
  Then ``$CONTEXT`` and the wildcard ``*`` have the lowest priority.

``UDM modules in permissions``
  In permissions you can define UDM module names or a wildcard ``*``.
  If there is a permission for the UDM module of the target object,
  UCS uses it, otherwise it uses the ``*`` permission.

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
:file:`/etc/umc-udm-roles.json`.
For more information,
see :ref:`da-config-reference`
and :numref:`da-concepts-custom-roles-listing`.
You can set the role ``umc:udm:myadmin`` to user or group objects.

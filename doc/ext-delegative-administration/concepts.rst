.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-concepts:

********
Concepts
********

This section describes the concept behind roles and permissions
for the delegative administration of the *Directory Service* through UDM.

To follow along the concept,
you need to know the following definitions for some of the used terms in this document.

.. glossary::

   Actor
     Is the person or entity that wants to perform an operation.

   Target object
     Is the object in the LDAP directory on which an actor performs the operation.

   Permission
     Permissions define what the actor can do to a target object.
     Which properties the actor can see or modify
     and if the actor can create or remove objects.

   Condition
     Conditions either restrict or define the target objects.
     Permissions are granted if all conditions are met.
     See the following examples for what can constitute a condition:

     * The position of the target object in the *Directory Service* structure
     * The UDM type of the target object

   Role
     A role is basically a container for a list of conditions and permissions.
     The policy configuration defines roles.
     You can assign roles to user and group objects.
     For more information,
     see :ref:`da-config-reference`.

     Administrators can assign roles to user objects as ``guardianRoles``,
     or to group objects as ``guardianMemberRoles``.
     In group objects with a role assignment,
     all group member objects inherit the role of the group.

     To add the role ``udm:default-roles:domain-administrator`` to a user object,
     the command looks like :numref:`da-concepts-listing`.

     .. code-block:: console
        :caption: Add the ``domain-administrator`` role to a user object
        :name: da-concepts-listing

        $ udm users/user modify \
            --dn "$LDAP_DN" \
            --append guardianRoles="udm:default-roles:domain-administrator"

.. seealso::

   :external+guardian-doc:ref:`guardian-terminology`
      in :cite:t:`guardian-doc`
      for more background information about concepts and ideas behind this concept.

.. _da-concepts-context:

Basic idea
==========

With delegative administration for UDM we want to enable Administrators to
easily define roles and policies for what an actor can do in the *Directory Service*.

If activated, LDAP ACLs for actors will no longer apply, instead UDM checks
the authorization for the actor based on the actors roles and the current UDM
policy and will access the *Directory Service* with a privileged account.

For testing purposes you could add LDAP ACLs for an actor to deny access to
the LDAP completely, see :external+uv-developer-reference:ref:`settings-ldapacl`.
If this actor has roles and if there are UDM policies in
place that allow certain operations in the *Directory Service* for this role,
the actor will be able to perform these operations despite the LDAP ACLs.

Roles and context
=================

A string defines a role.
It consists of the following parts,
separated by colons, for example ``udm:default-roles:domain-admin``.

* The name of the service for whom this role applies to.
* A namespace to separate default and custom roles.
* A name.

Roles may have an optional context, such as the context of position.
This context is an LDAP distinguished name (DN), without the LDAP base.
It specifies the position in the *Directory Service* to which the role applies.

A role context definition has the following elements:

``&``
   is the separator between the role and the context.

``udm:contexts:position``
   is the context name

``=``
   is the separator between the context name and the context value.

``ou=bremen``
   is a position in the directory structure in form of an LDAP DN,
   without the LDAP base to which the role applies.
   The value ``ou=bremen`` is an example.

One example is the role ``udm:default-roles:organizational-unit-admin``.
This role has one definition for what it can do.
However, you may want to differentiate between different organizational units.

When you assign the role to an user object,
as shown in :numref:`da-concepts-context-listing`,
you can assign different contexts of position.

.. code-block::
   :caption: Schema for setting a context when assigning the role
   :name: da-concepts-context-listing

   user1 → guardianRoles → udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen
   user2 → guardianRoles → udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=berlin

The ``user1`` and ``user2`` user objects have the same permissions.
The permissions derive from the role ``udm:default-roles:organizational-unit-admin``.
However, the permissions apply for different positions in the *Directory Service*:

* ``user1`` is ``organizational-unit-admin`` for the container :samp:`ou=bremen,{$ldap_base}`.
* ``user2`` is ``organizational-unit-admin`` for the container :samp:`ou=berlin,{$ldap_base}`.

.. important::

   Not every role considers the context.
   Whether a context is meaningful for a role depends on the configuration of the role.

   For example, the role ``udm:default-roles:domain-administrator`` doesn't evaluate the context;
   therefore, a context for this role has no effect.
   Conversely, without a context,
   the role ``udm:default-roles:organizational-unit-admin`` is essentially useless.

.. _da-concepts-role-definition:

Definition of roles
===================

Bringing all the concepts together,
:numref:`da-concepts-role-definition-listing`
shows an example for a generic form of a role definition.

.. code-block::
   :caption: Example for role configuration
   :name: da-concepts-role-definition-listing

   access by role="<ROLE>" [context="udm:contexts:position"]
     to objecttype="<UDM_MODULE>" [position.subtree|base|one="<POSITION>"]
       grant actions="<ACTIONS>"
       grant properties="<OBJECT_PROPERTY>" permission="<PERMISSION>"

.. note::

   Values for ``objecttype`` and ``properties`` are names of UDM objects and
   UDM properties, like ``users/user`` or ``username``, not LDAP object classes or
   LDAP attributes.

The following list explains the elements from
:numref:`da-concepts-role-definition-listing`.

``access by``
   clauses describe the actor roles and which permissions are granted.
   You can specify multiple ``acces by`` clauses.

``to``
   clauses describe the target objects based on conditions like UDM object type and position.
   You can specify multiple ``to`` clauses within on ``access by`` clause.

``grant``
   clauses allow actions such as read or write
   and access to properties of UDM objects.

:samp:`role={<ROLE>}`
   Name of the role.
   The value is any string, but must contain two colons, such as
   ``udm:default-roles:organizational-unit-admin``.

:samp:`context="udm:contexts:position"`
   Defines a context of a position.
   You may use it as value for the position condition,
   see :ref:`da-concepts-context`

:samp:`to.objecttype={<UDM_MODULE>}`
   Restrict access rules to this type of UDM module.
   Value is the name of a UDM object,
   such as ``users/user`` or the wildcard ``*`` that matches every UDM object.

:samp:`to.position.subtree|base|one={<POSITION>}`
   Restrict access rules to this position in the LDAP tree, including the
   scope.

   :``subtree``: Permissions apply for this position and everything below this position.

   :``base``: Permissions apply only for the object that represents this position.

   :``one``: Permissions apply for this position and immediate subordinates.

   Position can have to following values:

   :``LDAP_DN``: Any position the *Directory Service* in format of a distinguished name (DN).

   :``{ldap_base}``: A placeholder for the actual LDAP base.

   :``{context}``: A placeholder for the current context.

   For example, ``to.position.subtree="cn=users,ou=berlin,{ldap_base}"``.
   The example restricts the access rule to objects in and below the position
   ``cn=users,ou=berlin,{ldap_base}`` in the *Directory Service*.

:samp:`grant.actions={<ACTIONS>}`
   You can grant actions to a role
   and define what an actor can do to a target.
   The value is a comma-separated list of the following values:

   * ``search``
   * ``read``
   * ``create``
   * ``modify``
   * ``rename``
   * ``remove``
   * ``move``
   * ``report-create``
   * or the wildcard ``*``

:samp:`grant.properties={<PROPERTIES>}`
   Grant access to these UDM properties.
   The value is a comma-separated list of UDM properties.

   For example: ``jpegPhoto,e-mail,phone,roomnumber,departmentNumber, or the wildcard "*"``

:samp:`grant.properties.permission={<PERMISSION>}`
   Grant these permissions for the previously defined properties.
   The value is a comma-separated list of the following values:

   * ``read``
   * ``search``
   * ``write``
   * ``readonly``
   * ``writeonly``
   * ``none``
   * or the wildcard ``*``

.. _da-concepts-role-definition-examples:

Examples for role definitions
=============================

A more advanced example is a role that can update the password for user objects
within a certain context or organizational unit.
This role has permission to:

* Read the LDAP base.

* Read the container objects ``cn``, ``ou``,
  and groups in the position defined by the role's context.

* Modify the password of user objects in the position defined by the role's context.

* Read some UDM settings objects, necessary for UMC to provide meaning defaults values.

.. code-block::
   :caption: Default definition for ``udm:default-roles:domain-administrator`` role
   :name: da-concepts-example-domainadmin-listing

   # Domain Administrators
   access by role="udm:default-roles:domain-administrator"
     description="Domain Admins are allowed to do anything in the whole domain"
     to objecttype="*"
       grant actions="*"
       grant properties="*" permission="write"

:numref:`da-concepts-example-helpdesk-listing`
is a more advanced example is a role that can update the password for user objects
within a certain context or organizational unit.
This role has permission to:

* Read the LDAP base.

* Read the container objects ``cn``, ``ou``,
  and groups in the position defined by the role's context.

* Modify the password of user objects in the position defined by the role's context.

.. code-block::
   :caption: Default definition for ``udm:default-roles:helpdesk-operator`` role
   :name: da-concepts-example-helpdesk-listing

   access by role="udm:default-roles:helpdesk-operator" context="udm:contexts:position"

     # LDAP Base
     to objecttype="container/dc" position.base="{ldap_base}"
       grant actions="search,read"
       grant properties="*" permission="read"

     # read container ou/cn in context
     to objecttype="container/ou" position.subtree="{context}"
       grant actions="search,read"
       grant properties="*" permission="read"
     to objecttype="container/cn" position.subtree="{context}"
       grant actions="search,read"
       grant properties="*" permission="read"

     # read groups permissions in context
     to objecttype="groups/group" position.subtree="{context}"
       grant actions="search,read"
       grant properties="name" permission="read"

     # update passwords of users in context
     to objecttype="users/user" position.subtree="{context}"
       grant actions="search,read,modify"
       grant properties="overridePWHistory,overridePWLength,unlock,password" permission="write"
       grant properties="password" permission="writeonly"

The *Helpdesk Operator* role in
:numref:`da-concepts-example-helpdesk-listing`
uses the ``context`` feature.
When you assign the role to a user object,
you also have to set the role's context, such as
``udm:default-roles:helpdesk-operator&udm:contexts:position=ou=bremen``.
A user with this role can modify the password property of users in
``ou=bremen,ldap_base`` of the *Directory Service*.

.. _da-concepts-priorities:

Evaluation of permissions
=========================

The evaluation of permissions doesn't follow a particular order.
Permissions can't be revoked after they're granted.
The following exceptions to this rule exist:

``Wildcards``
  Wildcards have a lower priority than a more specific rule or configuration.
  :numref:`da-concepts-priorities-wildcards-listing` shows an example.
  It defines ``write`` permission for everything, except for ``foobar``.

  .. code-block::
     :name: da-concepts-priorities-wildcards-listing
     :caption: Example for wildcards

     grant properties="*" permission="write"
     grant properties="foobar" permission="read"

``Permissions``
  Permissions that deny something with the value ``none`` have a higher priority
  than permissions that allow things.
  :numref:`da-concepts-priorities-permissions-listing` shows an example.
  It grants ``write`` permission for every property, except for ``foobar``.

  .. code-block::
     :name: da-concepts-priorities-permissions-listing
     :caption: Example for Permissions

     grant properties="*" permission="write"
     grant properties="foobar" permission="none"

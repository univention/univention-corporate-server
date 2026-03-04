.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-setup-roles:

Configure role assignment strategies
=====================================

With the trust relationship established between Nubus Keycloak and your upstream IdP,
you must configure how Nubus assigns guardian roles to federated users.
Two approaches are available for role assignment.

Direct role attribute approach
   The upstream IAM stores guardian roles directly in a user attribute
   and transfers them during authentication.
   This approach requires the upstream IAM to support a custom attribute
   but minimizes mapping complexity.
   See :ref:`fed-auth-setup-roles-direct`.

Group-based role assignment
   Nubus derives guardian roles from the user's group memberships in the upstream IAM.
   This approach avoids schema extensions
   but requires additional mapping configuration in both IdPs.
   See :ref:`fed-auth-setup-roles-groups`.

Choosing between the approaches depends on your upstream IAM capabilities.
Use the direct approach if your upstream IAM allows custom attributes.
Use the group-based approach if schema extensions aren't possible,
or you prefer managing roles through group membership.

.. important::

   You must choose **one** of these approaches for your environment.
   The two approaches are mutually exclusive alternatives,
   not sequential configuration steps.

.. _fed-auth-setup-roles-direct:

Direct role attribute approach
------------------------------

Use this approach when your upstream IAM provides guardian roles
as a user attribute named ``nubus_roles``.
The upstream IAM must expose ``nubus_roles`` as a multi-value attribute.
You must forward this attribute through the entire authentication chain.

This configuration requires minimal mapping logic because the
upstream IAM provides the roles.
However, your upstream IAM must support a suitable attribute for
storing the Nubus guardian roles.

.. _fed-auth-setup-roles-direct-upstream:

Upstream IdP
~~~~~~~~~~~~

Configure the upstream identity provider to include the ``nubus_roles`` attribute in
the OpenID Connect token.
Create an additional mapper for the OIDC client used for the trust
relationship with Nubus:

``User Attribute`` mapper
   * **User Attribute:** ``nubus_roles``
   * **Token Claim Name:** ``nubus_roles``
   * **Claim JSON Type:** ``String``
   * **Multivalued:** ``true``

   This mapper ensures that the upstream IdP includes the ``nubus_roles`` claim
   in the token returned after authentication.

.. _fed-auth-setup-roles-direct-nubus:

Nubus IdP
~~~~~~~~~

Nubus Keycloak must import the claim that the upstream IdP provides.
Create an ``Attribute Importer`` mapper in the OIDC identity provider
configuration:

``Attribute Importer`` mapper
   * **Claim:** ``nubus_roles``
   * **User Attribute:** ``nubus_roles``
   * **Sync mode:** ``force``

   This mapper stores the role information from the upstream IdP
   as a user attribute in the Nubus Keycloak user object.

.. _fed-auth-setup-roles-direct-umc:

UMC OIDC clients
~~~~~~~~~~~~~~~~

You must forward the roles to the *Management UI* (UMC).
For each UMC OIDC client, create a ``User Attribute`` mapper:

``User Attribute`` mapper
   * **User Attribute:** ``nubus_roles``
   * **Token Claim Name:** ``nubus_roles``
   * **Claim JSON Type:** ``String``
   * **Multivalued:** ``true``

.. _fed-auth-setup-roles-direct-flow:

Authentication flow for direct roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With this configuration,
the role information flows through the system as follows:

#. The user signs in at the upstream IdP.

#. The upstream IdP reads the ``nubus_roles`` attribute from the upstream IAM.

#. The upstream IdP includes the roles in the OIDC token as the claim ``nubus_roles``.

#. Nubus Keycloak imports this claim into the local user attribute ``nubus_roles``.

#. The UMC OIDC client mapper includes this attribute in the token issued to UMC.

#. The *Management UI* (UMC) reads the ``nubus_roles`` claim
   and uses the corresponding guardian roles for the session.

.. _fed-auth-setup-roles-groups:

Group-based role assignment approach
-------------------------------------

Use this approach when you can't extend your upstream IAM with custom attributes.
In this model:

* Users in the upstream IAM are members of groups.
* Each group represents a specific Nubus :term:`Guardian role <Role>`.
* The upstream IdP sends the user's group memberships during sign-in.
* Nubus Keycloak maps these groups to corresponding groups in the Nubus IdP.
* These Nubus groups contain the guardian role definitions.

Role management remains fully controlled by group membership in the upstream IAM.

The group-based approach avoids schema extensions in the upstream IAM,
making it suitable for environments where you can't add custom attributes.
Group membership centralizes role management and allows dynamic role updates.

However, this approach requires more complex mapping configuration
in both the upstream IdP and Nubus Keycloak.
For environments with many roles, consider automating the configuration
to reduce maintenance burden.

.. _fed-auth-setup-roles-groups-example:

Example structure
~~~~~~~~~~~~~~~~~

The example in :numref:`fed-auth-group-structure`
illustrates the mapping between upstream groups and Nubus guardian roles.
During sign-in,
membership in ``/nubus_manager_ou1`` in the upstream IdP
results in membership in the group ``upstream_nubus_manager_ou1`` in Nubus Keycloak.
This group provides the guardian role for the *Management UI* (UMC).

The configuration requires changes in both the upstream IdP and the Nubus IdP.

.. code-block:: console
   :caption: Example group mapping
   :name: fed-auth-group-structure

   Upstream IdP:
     User: manager-ou1
     Group membership: nubus_manager_ou1
     Path: /nubus_manager_ou1

   Nubus IdP:
     Group: upstream_nubus_manager_ou1
     Attribute: nubus_roles
     Value: udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou1,dc=ucs,dc=test

.. _fed-auth-setup-roles-groups-upstream:

Upstream IdP configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure the upstream IdP to include group membership information in the issued
OpenID Connect tokens.

#. Create a client scope named ``groups``.

#. Add a mapper of type ``Group Membership`` that maps the user's groups
   to the token claim ``groups``.
#. Add the ``groups`` scope as a **default client scope** for the OIDC client
   that you use for the trust relationship with Nubus.

After this configuration,
the upstream IdP includes a claim similar to
:numref:`fed-auth-setup-roles-groups-upstream-claim`.

.. code-block:: json
   :caption: Claim in the upstream IdP
   :name: fed-auth-setup-roles-groups-upstream-claim

   {
     "groups": [
       "/nubus_manager_ou1"
     ]
   }

.. _fed-auth-setup-roles-groups-nubus:

Nubus IdP configuration
~~~~~~~~~~~~~~~~~~~~~~~

In Nubus Keycloak, you must map the upstream group memberships to local groups.
These mappers make users who sign in through the upstream IdP members
of the corresponding group in Nubus Keycloak.

#. Create a client scope named ``groups``.

#. Add the scope ``groups`` to the list of requested scopes
   in the OIDC identity provider configuration.

#. For each upstream group that represents a Nubus role,
   create a local group and add the ``nubus_roles`` attribute.

   ``Group``
      * **Name:** ``upstream_nubus_manager_ou1``
      * **Attribute**: ``nubus_roles``
      * **Value**: ``udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou1,dc=ucs,dc=test``

#. For each upstream group that represents a Nubus role,
   create a mapper of type ``Advanced Claim to Group``.

   ``Advanced Claim to Group`` mapper
      * **Name:** ``group_/nubus_manager_ou1``
      * **Sync mode override:** ``Force``
      * **Claims key:** ``groups``
      * **Claims value:** ``/nubus_manager_ou1``
      * **Group:** ``upstream_nubus_manager_ou1``

.. _fed-auth-setup-roles-groups-umc:

Providing guardian roles to UMC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The mappers in the previous step :ref:`fed-auth-setup-roles-groups-nubus`
synchronize group membership from the upstream IAM
to local groups in the Nubus IdP, adding role information.
You must include these roles in the tokens issued to the *Management UI* (UMC).

For each UMC OIDC client, create a client mapper that aggregates the
``nubus_roles`` attributes from all user groups.

``User Attribute`` mapper:
   * **Name:** ``nubus_roles_from_groups``
   * **User Attribute:** ``nubus_roles``
   * **Token Claim Name:** ``nubus_roles``
   * **Claim JSON Type:** ``String``
   * **Multivalued:** ``true``
   * **Aggregate attribute values:** ``true``

.. _fed-auth-setup-roles-groups-flow:

Sign-in flow for group-based roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With this configuration,
the sign-in process works as follows:

#. The user signs in to the *Management UI* (UMC).
#. Nubus Keycloak redirects the user to the upstream IdP.
#. The upstream IdP signs the user in and returns the ``groups`` claim.
#. Nubus Keycloak maps the upstream groups to local groups.
#. The local groups contain the ``nubus_roles`` attribute.
#. The UMC client mapper aggregates these roles.
#. Nubus sends the resulting ``nubus_roles`` claim to the *Management UI* (UMC).
#. The *Management UI* (UMC) applies the roles for delegative administration in the session.

.. _fed-auth-setup-roles-groups-automation:

Automating the configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In environments with many roles, manually creating the group mappings and
mappers is difficult to maintain.
A common approach is to define a configuration
that describes the mapping between upstream groups and Nubus roles
and generate the required objects automatically.

See the example configuration in :numref:`fed-auth-roles-from-group-example-config`.
A script can use such a configuration to automatically create:

* the corresponding groups in Nubus Keycloak.
* the ``nubus_roles`` attributes on the group.
* the required ``Advanced Claim to Group`` mappers.

.. code-block:: console
   :caption: Example mapping configuration
   :name: fed-auth-roles-from-group-example-config

   [
     {
       "upstream-group-name": "/nubus_manager_ou1",
       "group-name": "upstream_nubus_manager_ou1",
       "nubus-roles": "udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou1,dc=ucs,dc=test"
     },
     {
       "upstream-group-name": "/nubus_manager_ou2",
       "group-name": "upstream_nubus_manager_ou2",
       "nubus-roles": "udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou2,dc=ucs,dc=test"
     }
   ]


.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-troubleshooting:

Troubleshooting federated authentication
========================================

This section covers common problems you may encounter
when configuring or using federated authentication.
Each subsection describes a symptom, its likely cause, and steps to resolve it.

If you can't find a solution here,
review the logs of the relevant component first:

* For sign-in failures, review the logs of the upstream IdP or IAM.

* For UMC permission issues, review the Keycloak realm ``ucs``
  and the *UMC policy* on the ``federated_accounts`` container.

* For missing roles, review the token content using the **Keycloak Admin Console**.

.. _fed-auth-troubleshooting-authentication-fails:

Sign-in fails
-------------

The upstream IdP handles sign-in.
If the sign-in process fails before the upstream IdP redirects the browser back to Nubus,
review the logs of the upstream IAM or identity provider.

After a successful sign-in,
Nubus creates a ``users/federated_account`` object.

You can verify this with the command in
:numref:`fed-auth-troubleshooting-authentication-fails-command-listing`
and the output similar to
:numref:`fed-auth-troubleshooting-authentication-fails-command-output-listing`.
If Nubus creates no object, verify the attribute mapping for ``nubus_id``.

.. code-block:: console
   :caption: Verify federated accounts
   :name: fed-auth-troubleshooting-authentication-fails-command-listing

   $ udm users/federated_account list

.. code-block:: console
   :caption: Example output
   :name: fed-auth-troubleshooting-authentication-fails-command-output-listing

   DN: univentionObjectIdentifier=4f0fdab5-2979-4b25-87b7-5ecdf623547e,cn=federated_accounts,cn=univention,{ldap_base}
   description: None
   preferred_username: None
   univentionObjectIdentifier: 4f0fdab5-2979-4b25-87b7-5ecdf623547e

.. _fed-auth-troubleshooting-no-modules:

No management modules are visible after sign-in
-----------------------------------------------

If the sign-in succeeds but no management modules are visible,
the federated account has no UMC permissions.

Verify that the ``federated_accounts`` container has a *UMC policy* attached
and that it allows access to the required modules.
See the example configuration in :numref:`fed-auth-troubleshooting-no-modules-listing`.

.. code-block:: console
   :caption: Example configuration
   :name: fed-auth-troubleshooting-no-modules-listing

   DN: cn=federated_accounts,cn=univention,{ldap_base}
   type: container/cn
   univentionPolicyReference: cn=organizational-unit-admins,cn=UMC,cn=policies,{ldap_base}

   DN: cn=organizational-unit-admins,cn=UMC,cn=policies,{ldap_base}
   type: policies/umc
   allow: cn=udm-all,cn=operations,cn=UMC,cn=univention,{ldap_base}

.. _fed-auth-troubleshooting-authorization:

Authorization doesn't work
--------------------------

If the user can sign in but can't create, modify, or search UDM objects,
the ``nubus_roles`` claim is missing or incorrect.

To verify the token content:

#. Open the **Keycloak Admin Console**.
#. Navigate to the UMC client in the ``ucs`` realm.
#. Open **Client scopes → Evaluate**.
#. Enter the username and generate the token preview.

The generated user info must contain the following claims.

* ``nubus_id``
* ``nubus_federated_account``
* ``nubus_roles``

See the example in :numref:`fed-auth-troubleshooting-authorization-listing`.
If the ``nubus_roles`` claim is missing, verify the role mapping configuration
in the upstream IdP or the group-to-role mapping in Nubus Keycloak.

.. code-block:: json
   :caption: Example token content
   :name: fed-auth-troubleshooting-authorization-listing

   {
     "uid": "4f0fdab5-2979-4b25-87b7-5ecdf623547e",
     "nubus_roles": [
       "udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou1,dc=ucs,dc=test"
     ],
     "nubus_id": "4f0fdab5-2979-4b25-87b7-5ecdf623547e",
     "nubus_federated_account": true
   }



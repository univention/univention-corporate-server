.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-establish-trust:

Establish trust between Nubus and the upstream IdP
===================================================

Next, establish a trust relationship between Nubus Keycloak
and the upstream identity provider.

The exact configuration depends on the upstream IAM and identity provider.
This section provides a generic overview using a concrete example where
both identity providers are **Keycloak** instances and both establish trust
using **OpenID Connect (OIDC)**.
All configuration steps in this section refer to the **Keycloak Admin Console**.

For detailed information about identity brokering in Keycloak,
see `Integrating identity providers in <https://www.keycloak.org/docs/latest/server_admin/#_identity_broker>`_
in :cite:t:`keycloak-admin-guide`.

.. _fed-auth-establish-trust-upstream:

Upstream IdP configuration
--------------------------

First, create an **OIDC client** in the upstream identity provider that
Nubus Keycloak uses for authentication.

This client must provide a stable identifier for each user.
Map this identifier to the claim ``nubus_id``.
Suitable identifiers include:

* ``guid`` in Active Directory
* ``univentionObjectIdentifier`` in Nubus
* another globally unique user identifier

Configure a **User Attribute mapper** for the client:

``User Attribute`` mapper
   * **User Attribute:** The attribute containing the unique user identifier
   * **Token Claim Name:** ``nubus_id``
   * **Claim JSON Type:** ``String``

   This mapper ensures that the upstream IdP includes the ``nubus_id`` claim in
   the issued OIDC token.

.. _fed-auth-establish-trust-nubus:

Nubus Keycloak identity provider configuration
----------------------------------------------

In the Nubus Keycloak realm ``ucs``,
create an *OpenID Connect Identity Provider* pointing to the upstream IdP.
In addition to the standard OIDC settings,
you must configure several mappers to correctly handle federated users.

``Hardcoded Attribute`` mapper
   * **User Attribute:** ``nubus_federated_account``
   * **Attribute Value:** ``true``

   This attribute marks the user as a federated account
   so that the *Management UI* (UMC) can apply the appropriate handling.

``Attribute Importer`` mapper
   * **Claim:** ``nubus_id``
   * **User Attribute:** ``nubus_id``
   * **Sync mode:** ``force``

   This mapper imports the unique identifier from the upstream IdP into the local
   Keycloak user object.

``Username Template Importer`` mapper
   * **Template:** ``${ALIAS}.${CLAIM.nubus_id}``
   * **Target:** ``local``

   With this configuration, the generated username combines
   the identity provider alias and the upstream user identifier, for example:

   .. code-block:: console

      myUpstreamIDP.4f0fdab5-2979-4b25-87b7-5ecdf623547e

Keycloak requires several user attributes such as ``email``,
``firstName``, and ``lastName``.
Because this feature minimizes the amount of user data transferred from the upstream IAM,
you populate these attributes with the value of ``nubus_id``.
Create the following ``Attribute Importer`` mappers:

``Attribute Importer`` mapper
   * **Name:** ``override_email``
   * **Claim:** ``nubus_id``
   * **User Attribute:** ``email``
   * **Sync mode:** ``force``

``Attribute Importer`` mapper
   * **Name:** ``override_lastname``
   * **Claim:** ``nubus_id``
   * **User Attribute:** ``lastName``
   * **Sync mode:** ``force``

``Attribute Importer`` mapper
   * **Name:** ``override_firstname``
   * **Claim:** ``nubus_id``
   * **User Attribute:** ``firstName``
   * **Sync mode:** ``force``

Because Keycloak populates the ``email`` attribute with a UUID instead of a valid
email address, you must relax the default Keycloak email validation.
To adjust the validation:

#. Open *Realm settings* in the ``ucs`` realm.
#. Navigate to *User profile*.
#. Edit the ``email`` attribute.
#. Remove the ``email`` validation rule.

This allows Keycloak to store UUID values in the ``email`` attribute.

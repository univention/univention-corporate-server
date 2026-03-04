.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-configure-umc-client:

Configure the UMC OIDC client
=============================

When you enable OIDC single sign-on for the *Management UI*,
Nubus automatically creates one or more OIDC clients in the Keycloak realm ``ucs``.
The UMC servers use these clients to authenticate users.

For federated authentication,
you must include additional claims in the OIDC token issued to the *Management UI*.
These claims allow the *Management UI* to:

* identify federated users.
* associate the session with the upstream identity.
* apply delegative administration roles.

To provide this information,
you must configure additional client mappers on **all UMC OIDC clients** in the ``ucs`` realm.

``User Attribute`` mapper
   * **User Attribute:** ``nubus_id``
   * **Token Claim Name:** ``nubus_id``
   * **Claim JSON Type:** ``String``

   This mapper exposes the upstream user identifier to the *Management UI* (UMC).

``User Attribute`` mapper
   * **User Attribute:** ``nubus_federated_account``
   * **Token Claim Name:** ``nubus_federated_account``
   * **Claim JSON Type:** ``boolean``

   This mapper indicates whether the authenticated user is a federated account.

``User Attribute`` mapper
   * **User Attribute:** ``nubus_id``
   * **Token Claim Name:** ``uid``
   * **Claim JSON Type:** ``String``

   This mapper maps the upstream identifier to the ``uid`` claim used by the *Management UI* (UMC).

.. note::

   The *Management UI* (UMC) internally expects the ``uid`` claim
   to identify the user session.
   For federated users, Nubus derives this value from ``nubus_id``.

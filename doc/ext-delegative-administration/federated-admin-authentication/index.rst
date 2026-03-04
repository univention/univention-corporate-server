.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-overview:

*******************************************
Federated authentication for administrators
*******************************************

This section describes how to configure and operate federated authentication
for administrators in Nubus for UCS
that authenticates and authorizes administrative user accounts
with an external identity and access management (IAM).

:ref:`fed-auth-concepts`
   Background, data protection, Keycloak mappers,
   prerequisites, and configuration sequence.

:ref:`fed-auth-configure-nubus`
   Configure Nubus for UCS
   to accept federated accounts.

:ref:`fed-auth-establish-trust`
   Establish a trust relationship
   between Nubus Keycloak and your upstream identity provider.

:ref:`fed-auth-configure-umc-client`
   Configure the UMC OIDC client
   to pass identity and role information to the *Management UI*.

:ref:`fed-auth-setup-roles`
   Choose and configure how federated users
   receive guardian roles: direct attribute or group-based assignment.

:ref:`fed-auth-verification`
   Test and confirm
   that federated authentication works.

:ref:`fed-auth-manage-administrators`
   Add, remove, and update administrators,
   and prepare for upstream IAM outages.

:ref:`fed-auth-troubleshooting`
   Diagnose and resolve common sign-in,
   permission, and authorization issues.


.. toctree::
   :caption: Contents

   concept
   setup
   trust
   oidc
   role-strategies
   verification
   operation
   troubleshooting

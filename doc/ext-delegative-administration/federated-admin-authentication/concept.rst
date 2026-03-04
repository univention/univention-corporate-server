.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-concepts:

Concepts
========

Federated authentication lets administrators sign in to Nubus
using their upstream identity provider (IdP),
such as Active Directory or another identity management system.
Regular users continue to sign in to Nubus directly.
Only administrator accounts sign in through the upstream IAM.
Administrator accounts remain in your upstream IAM.
Nubus verifies each administrator sign-in against the upstream IAM,
then grants permissions based on roles defined in Nubus.

This approach keeps administrator accounts separate from regular user accounts
and removes the need to maintain administrator accounts in Nubus.

.. _fed-auth-basic-idea:

Basic idea
----------

The technical foundation of this feature is a trust relationship
between Nubus Keycloak and the upstream identity provider.
This trust relationship allows users from the upstream IAM
to sign in to Nubus without a local user account.

For authorization, Nubus requires information about the roles assigned to the user.
The upstream IAM must provide this information as guardian role strings
for delegative administration.
Nubus evaluates these roles during the UDM authorization process for the current session.

From a technical perspective,
the authentication flow is as follows:

#. The user starts a sign-in to the *Management UI* using OpenID Connect (OIDC).
#. Nubus Keycloak redirects the request to the upstream identity provider.
#. The user selects the upstream IdP.
#. The upstream IdP authenticates the user.
#. The upstream IdP returns an access token containing role information.
#. The upstream IdP redirects the browser back to the UMC service of the *Management UI*.
#. The *Management UI* reads the roles from the access token and assigns them to the session.
#. The user signs in to the *Management UI* with permissions derived from these roles.

In this scenario, **Nubus creates no user account**.
The upstream IdP provides authorization information
that Nubus trusts and uses only for the current session.
To ensure traceability of administrative actions, Nubus creates a technical
object during the first sign-in.
See :ref:`fed-auth-data-protection` for more details.

.. _fed-auth-data-protection:

Data protection
---------------

A key characteristic of this feature is that accounts
don't exist as user accounts in Nubus.
Authentication without the upstream IdP isn't possible.
Nubus permanently stores **only minimal information** about federated identities.

To ensure traceability of changes, Nubus stores the identifier from the
upstream IAM in a UDM object of type ``users/federated_account``.
Its primary purpose is to ensure the uniqueness of the identifier within Nubus
and to prevent its reuse.
This object isn't a real user account:

* It has no password.
* It has no usable username.
* You can't use it to authenticate.

Additionally, the Nubus Keycloak IdP stores temporary user objects for the
federated identities.
These objects have no password and Nubus can delete them at any time.
Nubus recreates them automatically when the user signs in again
through the upstream IdP.

The upstream IAM transfers the following information to Nubus during
authentication:

:``User identifier``: A unique identifier (ID) for the user. Nubus stores this value permanently.

:``Role information``: Information used for authorization.
   Nubus uses this information only for the session and doesn't store it.

:``Username`` (optional): A username used as the display name in the UMC session.
   Nubus doesn't store this value.

.. _fed-auth-mappers-overview:

Understanding Keycloak mappers
------------------------------

Keycloak mappers transform identity information between systems.
They control what data flows between the upstream IdP, Nubus Keycloak,
and the *Management UI* (UMC).

This guide uses the following mapper types.
Each configuration section shows the specific mappers needed for that phase.

User Attribute mapper
   Includes a user attribute in the OIDC token as a claim.

Hardcoded Attribute mapper
   Adds a static value to the OIDC token for all users.

Attribute Importer mapper
   Imports a claim from the upstream IdP and stores it as a local user attribute.

Username Template Importer mapper
   Generates a username based on a template.

Group Membership mapper
   Includes user group memberships in the OIDC token.

Advanced Claim to Group mapper
   Maps incoming claims to local groups.

.. _fed-auth-prerequisites:

Technical prerequisites
-----------------------

You need the following components for federated authentication for administrators:

* Nubus for UCS with the :program:`Keycloak` app installed.

* An upstream IdP that supports OpenID Connect.

* Single sign-on configured using OIDC in the *Management UI*.

* Delegative administration enabled for the *Management UI* (UMC).
  See :ref:`da-setup-test-env`.

* A globally unique identifier (UUID) for user objects in the upstream IAM.

* :term:`Guardian role <Role>` information provided by the upstream IAM.

  You can provide guardian roles either as a direct attribute in the
  upstream IAM or by deriving them from other data, such as group membership.

.. important::

   Federated authentication for administrators works only
   on the Nubus for UCS system roles |UCSPRIMARYDN| and |UCSBACKUPDN|.

.. _fed-auth-setup-sequence:

Before you begin
----------------

Configuring this feature spans multiple systems in Nubus for UCS and your upstream IAM.
You must follow a specific order because later phases depend on
completing earlier phases first.

Configuration happens in the following phases.
Complete each phase before moving to the next:

#. Configure Nubus for UCS to accept federated accounts,
   enable LDAP support for federated identities,
   and set up Keycloak for OIDC authentication.

#. Establish trust between Nubus Keycloak and your upstream identity provider
   using OpenID Connect.
   This phase involves working with your upstream IAM administrator.

#. Configure the UMC OIDC client to include the necessary claims and mappers.
   This ensures the *Management UI* (UMC) receives role information from the upstream IdP.

#. Configure how federated users receive guardian roles.
   Your upstream IAM capabilities determine whether you apply direct attribute
   mapping or group-based role derivation.
   You can use only one approach; they're mutually exclusive.
   See :ref:`fed-auth-setup-roles` for details.

When you encounter issues during setup,
see :ref:`fed-auth-troubleshooting` for guidance.

.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-configure-nubus:

Configure Nubus for UCS
=======================

This section covers the configuration steps in Nubus for UCS
to allow administrators to access the *Management UI* using federated authentication.

Because federated users don't exist as normal user objects in Nubus,
you must configure additional settings to ensure
that these accounts can access the *Management UI*
and that you can store the corresponding federated account objects in the LDAP directory service.

.. _fed-auth-configure-nubus-umc-permissions:

UMC permissions for federated accounts
---------------------------------------

As described in :ref:`da-limits`,
the *Management UI* doesn't support delegative administration directly.
Therefore, you must grant federated accounts the required UMC permissions through a policy.

To achieve this,
you store all federated account objects in a dedicated LDAP container
and apply a *UMC policy* to this container.

#. Create a container object of type ``container/cn`` with the name
   ``federated_accounts`` at the position :samp:`cn=univention,{ldap_base}`.
   This container serves two purposes:

   * It provides a dedicated location for federated account objects.
   * It grants UMC frontend permissions through the attached *UMC policy*.

#. Create a ``policies/umc`` policy that allows access to all management modules.

#. Configure the policy to allow the UMC operation set ``udm-all``.

#. Link the policy to the ``federated_accounts`` container.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-policies`
      in :cite:t:`uv-nubus-manual`
      for information about the *Policy* management module
      in the *Management UI*.

.. _fed-auth-configure-nubus-ldap:

Enable federated account support in LDAP
-----------------------------------------

To allow Nubus to authenticate federated accounts,
you must enable support for federated authorization identities
in the LDAP server configuration.

Run the command in :numref:`fed-auth-setup-ldap-server`
on all LDAP servers in your environment.
This configuration activates the authorization mapping that allows the
LDAP server to accept federated accounts that the identity provider authenticates.

.. code-block:: console
   :caption: Enable federated account authentication
   :name: fed-auth-setup-ldap-server

   $ ucr set ldap/authz-regexp/federated-accounts=yes
   $ systemctl restart slapd

.. _fed-auth-configure-nubus-keycloak:

Keycloak and single sign-on in the Management UI
------------------------------------------------

Federated authentication relies on OpenID Connect authentication through Keycloak.
Therefore, you must install and configure the following components:

* The *Keycloak* app in Nubus for UCS
* Single sign-on in the *Management UI* using OIDC

For detailed instructions,
see :external+uv-ucs-operation:ref:`management-interface-auth-sso-oidc`
in :cite:t:`uv-ucs-operation`.
After completing these steps,
Nubus can accept federated identities
from the upstream identity provider.


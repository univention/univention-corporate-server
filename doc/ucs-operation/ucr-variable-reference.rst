.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

**********************
UCR variable reference
**********************

This section provides a reference for UCR variables.

.. envvar:: portal/auth-mode

   Specifies the mechanism
   that the *Portal* uses to authenticate a user
   when clicking the login button in the *Portal* sidebar.
   For the values ``saml`` and ``oidc``
   the clients have to resolve the name of the SSO server
   and retrieve and trustworthy and valid certificate.

   :Default value: ``ucs``
   :Type: string
   :Possible values: ``saml``, ``oidc``, ``ucs``


.. envvar:: portal/reload-tabs-on-logout

   If activated,
   the Management UI sets up a persistent connection
   to the user's web browser.
   It notifies all Univention Portal browser tabs of a sign-out
   and causes them to reload.

   :Default value: ``false``
   :Type: boolean


.. envvar:: umc/http/processes

   Defines the number of *UMC Server* processes
   that Nubus for UCS starts in parallel.

   :Default value: ``1``
   :Type: Unsigned integer


.. envvar:: umc/http/session/timeout

   The web browser automatically closes the browser session
   after the defined time period in seconds.
   A new session requires a new sign-in

   :Default value: ``300``
   :Type: Unsigned integer


.. envvar:: umc/oidc/issuer

   Defines the OpenID provider issuer of this relying party entry.

   :Default value: None
   :Type: string


.. envvar:: umc/oidc/rp/server

   Defines the fully qualified domain name of the relying party for the *UMC Server*.
   If the variable is unset,
   Nubus for UCS uses the fully qualified domain name of the UCS system and all IP addresses.

   :Default value: None
   :Type: string


.. envvar:: umc/web/oidc/enabled

   If activated, the *UMC Server* tries the sign-in
   through OpenID Connect single sign-on
   before using a regular sign-in.

   .. TODO: Clarify support status.

      Source: https://git.knut.univention.de/fschneider/ucs-fixes/-/blob/5.2-0/management/univention-management-console/debian/univention-management-console-frontend.univention-config-registry-variables#L39-L44

      However, we recommend this setting in the documentation. How can't it be supported?

   .. caution::

      Univention doesn't support this setting.

   :Default value: ``false``
   :Type: boolean


.. envvar:: umc/web/sso/enabled

   If activated, the *UMC Server* tries the sign-in
   through single sign-on
   before using a regular sign-in.

   :Default value: None
   :Type: boolean

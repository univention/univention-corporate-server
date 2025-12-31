.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-single-sign-on:

Single sign-on
==============

UCS provides *single sign-on* functionality with a SAML 2.0 and OpenID Connect
compatible identity provider based on :program:`Keycloak`.
UCS doesn't install the identity provider by default.
If you need the identity provider, you need to install the app *Keycloak* through the |UCSAPPC|.
For information about how to install an app, see :ref:`computers-softwareselection`.

For an extensive documentation, describing the configuration of the :program:`Keycloak` app,
creating clients, and more, refer to :external+uv-keycloak-ref:ref:`doc-entry`
in the :cite:t:`ucs-keycloak-doc`.

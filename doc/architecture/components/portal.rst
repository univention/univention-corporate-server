.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _component-portal:

UCS portal
==========

.. index::
   pair: single sign-on; ucs portal
   see: portal; ucs portal

The UCS portal is the central entry point to |UCS| and home page for the work
place for domain users and administrators. The web page shows tiles with icons,
text, and web links to various services and applications of the domain and
external resources.

Every UCS system can have a portal page, regardless of its system role. A domain
can have multiple portal configurations with different content. The
portal configuration controls the following aspects:

* Which portal shows up on which UCS system in the domain?

* Which user groups see which tile on which UCS system?

Organizations can configure multiple portals. They can brand and customize them
individually to specific user groups.

.. admonition:: Continue reading

   :ref:`services-ucs-portal`
      for architecture details about the UCS portal service

.. seealso::

   :ref:`central-portal`
      for instructions about how to configure and customize the UCS portal page
      in :cite:t:`ucs-manual`

.. _component-portal-benefits:

Benefits
--------

For the portal as primary entry point to a UCS domain, users like administrators
or end users only need to remember or bookmark one web address. After login with
their web browser, users see their personal portal. Some tiles only show up
after login.

With single sign-on, users provide their credentials onetime per session and can
use services and apps without additional authentication.

.. _component-portal-sso:

Single sign-on for the UCS portal
---------------------------------

To use single sign-on with a service, the service needs to support and integrate
single sign-on in the UCS domain. UCS supports the standards SAML and OpenID
Connect.

.. TODO : Add references when ready to SAML, OpenID Connect and authentication.

   To use single sign-on with a service, the service needs to support and
   integrate single sign-on in the UCS domain. UCS supports the standards
   :ref:`SAML <services-authentication-saml>` and :ref:`OpenID Connect
   <services-authentication-openid-connect>`. For information about single
   sign-on, see :ref:`services-authentication`.

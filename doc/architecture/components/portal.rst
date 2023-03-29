.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

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

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

.. _central-general:

********
|UCSWEB|
********

.. highlight:: console

.. _fig-ucs-portal:

.. figure:: /images/portal.*
   :alt: UCS portal page

   UCS portal page

The |UCSWEB| is the central tool for managing a UCS domain as well as for
accessing installed applications of the domain.

The |UCSWEB| is divided into several pages which all have a similarly
designed header. Via the symbols in the top right, one may launch a search on
the current page (magnifier) or open the user menu (three bars) (login is
possible through the latter). The login at the web interface is done via a
central page once for all sub pages of UCS as well as for third party
applications as far as a web based *single sign-on* is supported
(:ref:`central-management-umc-login`).

Central starting point for users and administrators for all following
actions is the UCS portal page (cf. :numref:`fig-ucs-portal`). By
default, the portal page is available on all system roles and allows an
overview of all Apps and further services which are installed in the UCS
domain. All aspects of the portal page can be customized to match one's
needs (:ref:`central-portal`).

For environments with more than one server, an additional entry to a
server overview page is shown on the portal page. This sub page gives an
overview of all available UCS systems in the domain. It allows a fast
navigation to other systems in order to adjust local settings via UMC
modules.

UMC modules are the web based tool for the administration of the UCS
domain. There are various modules available for the administration of
the different aspects of a domain depending on the respective system
role. Installing additional software components may add new UMC modules
to the system. :ref:`central-user-interface` describes
their general operation.

The subsequent sections detail the usage of various aspects of the domain
management. :ref:`central-navigation` gives an overview of the LDAP directory
browser. The use of administrative settings via policies is discussed in
:ref:`central-policies`. How to extend the scope of function of the domain
administration is detailed in :ref:`central-extended-attrs`.
:ref:`central-cn-and-ous` details how containers and organizational units can be
used to structure the LDAP directory. :ref:`delegated-administration` explains
delegating administration rights to additional user groups.

In conclusion, the command line interface of the domain administration is
illustrated (:ref:`central-udm`), and the evaluation of domain data via the UCS
reporting function are explained (:ref:`central-reports`).


.. toctree::
   :caption: Chapter contents:

   introduction
   login
   portal
   umc
   ldap-browser
   policies
   extended-attributes
   user-defined-ldap-structures
   delegated-administration
   udm-command
   http-api-domain-management
   directory-reports
   lets-encrypt

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

.. _users-general:

***************
User management
***************

.. highlight:: console

UCS integrates central identity management. All user information are managed
centrally in UCS via the |UCSUMC| module :guilabel:`Users` and stored in the
LDAP directory service.

All the services integrated in the domain access the central account
information, i.e., the same username and password are used for the user login to
a Windows client as for the login on the IMAP server.

The domain-wide management of user data reduces the administrative efforts as
changes do not need to be subsequently configured on different individual
systems. Moreover, this also avoids subsequent errors arising from
inconsistencies between the individual datasets.

.. _users-types:

.. rubric:: User account types

There are three different types of user accounts in UCS:

1. **Normal user accounts** have all available properties. These users can log
   in to UCS or Windows systems and, depending on the configuration, also to the
   installed Apps. The users can be administered via the UMC module
   :guilabel:`Users` (see :ref:`users-management`).

2. **Address book entries** can be used to maintain internal or external contact
   information. These contacts can't sign in to UCS or Windows systems.
   Address book entries can be managed via the UMC module :guilabel:`Contacts`.

3. **Simple authentication account**: With a simple authentication account, a
   user object is created, which has only a username and a password. With this
   account, only authentication against the LDAP directory service is possible,
   but no login to UCS or Windows systems. Simple authentication accounts can be
   accessed via the UMC module :guilabel:`LDAP directory` (see
   :ref:`central-navigation`).

.. _users-recommendation-usernames:

.. rubric:: Recommendation for username definition

One very important and required attribute for user accounts is the *username*. To
avoid conflicts with the different tools handling user accounts in UCS, adhere
to the following recommendations for the definition of usernames:

* Only use lower case letters (``a-z``), digits (``0-9``) and the hyphen (``-``)
  from the ASCII character set for usernames.

* The username starts with a lower case letter from the ASCII character set. The
  hyphen is not allowed as last character.

* In UCS the username has at least a length of 4 characters and at most 20
  characters.

The recommendation results in the following regular expression:
``^[a-z][a-z0-9-]{2,18}[a-z0-9]$``.

Besides the recommendation, usernames also contain underscores (``_``) and upper
case ASCII letters in practice. Consider the recommendation as a guideline and
not a rule and keep potential side-effects in mind when defining usernames
outside the recommendation.

.. toctree::
   :caption: Chapter contents:

   umc
   user-activation-apps
   password-management
   password-settings-windows-clients
   user-self-service
   user-lockout
   user-templates
   last-bind-overlay

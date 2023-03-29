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

.. _users-app-activation:

User activation for apps
========================

Many apps from the App Center are compatible with the central identity
management in UCS. This allows system administrators to activate the
users for apps. In some cases, app specific settings for the user can be
made. This depends on the app and how it uses the identity management.

.. _user-app-activation:

.. figure:: /images/user_activation.*
   :alt: User activation for installed apps

   User activation for installed apps

Once an app with user activation is installed in the UCS environment, it will
appear with the logo in the :guilabel:`Apps` tab of the user in the UMC module
*Users*. With a tick in the checkbox the user is activated for the app. If the
app offers specific settings another tab with the name of the app will appear to
set these parameters. The app activation and the parameters are stored at the
user object in the LDAP directory service.

To withdraw a user activation for an app, it is sufficient to deselect
the checkbox.

When the app is uninstalled, the checkbox of the user activation for the
app is removed from the :guilabel:`Apps` tab of the user in
the UMC module.

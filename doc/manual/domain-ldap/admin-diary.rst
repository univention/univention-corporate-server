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

.. _domain-admindiary:

Protocol of activities in the domain
====================================

The :program:`Admin Diary` app provides the facility to log important events happening in
the domain. This includes among others:

* Creation, move, modification and deletion of users and other objects using
  |UCSUDM|

* Installation, update and deinstallation of apps

* Server password changes

* Start, end and eventual failures of domain joins

* Start and end of UCS updates

.. _domain-ldap-admindiary-list:

.. figure:: /images/admindiary-list.*
   :alt: View of events in Admin Diary

   View of events in Admin Diary

:numref:`domain-ldap-admindiary-list` shows, how events are shown in the UMC
module :guilabel:`Admin Diary`. By default the displayed entries are grouped by
week and can additionally be filtered through the search field. Selecting an
entry from the list opens a dialog showing additional details about the who and
when of the event, as shown in :numref:`domain-ldap-admindiary-detail`.
Moreover there is the possibility to comment each event.

.. _domain-ldap-admindiary-detail:

.. figure:: /images/admindiary-detail.*
   :alt: Detail view in Admin Diary

   Detail view in Admin Diary

The app consists of two components:

Admin Diary back end
   The back end must be installed on one system in the domain before the front end
   can be installed. It includes a customization for :program:`rsyslog` and
   writes into a central database, which defaults to PostgreSQL. If MariaDB or
   MySQL is already installed on the target system, it will be used instead of
   PostgreSQL.

Admin Diary front end
   Likewise the front end must be installed at least once, but more installations
   are also possible. The front end includes the UMC module :guilabel:`Admin
   Diary`, which is used to show and comment the entries. When installing it on
   a different host than where the back end is installed, access to the central
   database needs to be configured manually. The required steps for this are
   described in `Admin Diary - How to separate front end and back end
   <univention-kb-admin-diary-separate-frontend-backend_>`_.

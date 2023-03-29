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

.. _umc-architecture:

Architecture
============

The Univention Management Console service consists of four components.
The communication between these components is encrypted using SSL. The
architecture and the communication channels is shown in
:numref:`umc-api`.

.. _umc-api:

.. figure:: /images/umc-api.*
   :alt: UMC architecture and communication channels

   UMC architecture and communication channels

* The *UMC server* is the core component. It provides access to the modules and
  manages the connection and verifies that only authorized users gets access.
  The protocol used to communicate is the *Univention Management Console
  Protocol* (UMCP) in version 2.0.

* The *UMC HTTP server* is a small web server that provides HTTP access to the
  UMC server. It is used by the web front end.

* The *UMC module* processes are forked by the UMC server to provide a specific
  area of management tasks within a session.

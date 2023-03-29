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

.. _umc-framework:

Asynchronous framework
======================

All server-side components of the UMC service are based on the asynchronous
framework Python Notifier, that provides techniques for handling quasi parallel
tasks based on events. The framework follows three basic concepts:

Non-blocking sockets
   For servers that should handling several communication channels at a time
   have to use so called non-blocking sockets. This is an option that needs to
   be set for each socket, that should be management by the server. This is
   necessary to avoid blocking on read or write operations on the sockets.

Timer
   To perform tasks after a defined amount of time the framework provides an API
   to manage timer (one shot or periodically).

Signals
   To inform components within a process of a specific a events the framework
   provide the possibility to define signals. Components being interested in
   events may place a registration.

Further details, examples and a complete API documentation for Python Notifier
can be found at the `website of Python Notifier <univention-py-notifier_>`_.

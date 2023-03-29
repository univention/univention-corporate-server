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

.. _chap-ucr:

**************************
Univention Config Registry
**************************
.. index::
   single: config registry
   see: UCR; config registry
   see: registry; config registry

The |UCSUCR| (UCR) is a local mechanism, which is used on all UCS system roles
to consistently configure all services and applications. It consists of a
database, were the currently configured values are stored, and a mechanism to
trigger certain actions, when values are changed. This is mostly used to create
configuration files from templates by filling in the configured values. In
addition to using simple place holders its also possible to use Python code for
more advanced templates or to call external programs when values are changed.
UCR values can also be configured through an UDM policy in Univention directory
service (LDAP), which allows values to be set consistently for multiple hosts of
a domain.

.. toctree::

   usage
   configuration
   templates
   integration
   examples
   python3

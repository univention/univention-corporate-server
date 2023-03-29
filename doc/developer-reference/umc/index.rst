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

.. _chap-umc:

***********************************
Univention Management Console (UMC)
***********************************

.. index::
   single: management console
   see: Univention Management Console; management console
   see: UMC; management console

.. PMH: Bug #31269

The Univention Management Console (UMC) is a service that runs an all UCS
systems by default. This service provides access to several system information
and implements modules for management tasks. What modules are available on a UCS
system depends on the system role and the installed components. Each domain user
can log an to the service through a web interface. Depending on the access policies
for the user the visible modules for management tasks will differ.

In the following the technical details of the architecture and the Python and
JavaScript API for modules are described.

This chapter has the following content:

.. toctree::

   architecture
   framework
   umcp
   http-umc
   files
   local-system-module
   udm
   module
   python-migration
